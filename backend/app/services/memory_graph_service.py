import asyncio
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional

from langchain_core.messages import HumanMessage, SystemMessage

from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import (
    ConversationRepository,
    MemoryGraphRepository,
    MessageRepository,
)
from app.infrastructure.llm.gateway import LLMGateway

memory_graph_repo = MemoryGraphRepository()
message_repo = MessageRepository()
conv_repo = ConversationRepository()
title_llm = LLMGateway()


class MemoryGraphService:
    """Service handling graph-based memory storage, thread capture, linking, and context assembly."""

    async def suggest_title(
        self,
        conversation_id: int,
        kind: str,
        message_id: Optional[int] = None,
        up_to_message_id: Optional[int] = None,
    ) -> str:
        """Generate a concise node title with local Ollama, falling back to chat context."""
        with get_connection() as conn:
            conversation = conv_repo.get(conn, conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} does not exist")
            messages = message_repo.list_by_conversation(conn, conversation_id)

        if kind == "message":
            source = next((m for m in messages if m["id"] == message_id), None)
            if not source:
                raise ValueError(f"Message {message_id} not found in conversation {conversation_id}")
            content = source["content"]
            fallback = f"{conversation.get('title') or 'Conversation'}: {' '.join(content.split())[:64]}".strip()
        else:
            if up_to_message_id is not None and not any(
                message["id"] == up_to_message_id for message in messages
            ):
                raise ValueError(f"Message {up_to_message_id} not found in conversation {conversation_id}")
            selected = []
            for message in messages:
                selected.append(message)
                if up_to_message_id is not None and message["id"] == up_to_message_id:
                    break
            if not selected:
                raise ValueError(f"No messages found for conversation {conversation_id}")
            content = "\n\n".join(f"{m['role']}: {m['content']}" for m in selected)
            fallback = f"{conversation.get('title') or 'Conversation'} — saved thread"

        prompt_content = content[:6000]
        try:
            client = title_llm._get_client("ollama:qwen2.5-coder:7b", enable_tools=False)
            response = await asyncio.wait_for(
                client.ainvoke([
                    SystemMessage(content=(
                        "Create a clear, specific title for a saved memory from this conversation. "
                        "Use 3 to 8 words. Return only the title, with no quotes or explanation."
                    )),
                    HumanMessage(content=(
                        f"Conversation title: {conversation.get('title') or 'Untitled'}\n"
                        f"Memory type: {kind}\nConversation excerpt:\n{prompt_content}"
                    )),
                ]),
                timeout=25,
            )
            if isinstance(response.content, str):
                generated = response.content
            else:
                generated = "".join(
                    item if isinstance(item, str) else item.get("text", "")
                    for item in response.content
                    if isinstance(item, (str, dict))
                )
            title = " ".join(generated.strip().strip('"`').split())
            if title and len(title) <= 80 and "\n" not in generated.strip():
                return title
        except Exception:
            pass
        return fallback[:80]

    def capture_message(
        self,
        conversation_id: int,
        message_id: int,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        with get_connection() as conn:
            # Verify conversation exists first to prevent orphan nodes
            conv = conv_repo.get(conn, conversation_id)
            if not conv:
                raise ValueError(f"Conversation {conversation_id} does not exist")

            messages = message_repo.list_by_conversation(conn, conversation_id)
            target = next((m for m in messages if m["id"] == message_id), None)
            if not target:
                raise ValueError(f"Message {message_id} not found in conversation {conversation_id}")

            node_id = f"mem_msg_{message_id}_{uuid.uuid4().hex[:6]}"
            conversation_title = (conv.get("title") or "Conversation").strip()
            excerpt = " ".join(target["content"].split())[:64]
            default_title = title.strip() if title and title.strip() else (
                f"{conversation_title}: {excerpt}" if excerpt else f"Note from {conversation_title}"
            )
            node = memory_graph_repo.create_node(
                conn=conn,
                node_id=node_id,
                node_type="message",
                title=default_title,
                content=target["content"],
                source_conversation_id=conversation_id,
                source_message_id=message_id,
                metadata={"role": target["role"], "model": target.get("model")},
            )
            return node

    def capture_preference(
        self,
        conversation_id: int,
        message_id: int,
        content: str,
    ) -> Dict[str, Any]:
        with get_connection() as conn:
            conv = conv_repo.get(conn, conversation_id)
            if not conv:
                raise ValueError(f"Conversation {conversation_id} does not exist")

            node_id = f"mem_preference_{message_id}_{uuid.uuid4().hex[:8]}"
            node = memory_graph_repo.create_node(
                conn=conn,
                node_id=node_id,
                node_type="preference",
                title="Conversation preference",
                content=content,
                source_conversation_id=conversation_id,
                source_message_id=message_id,
                metadata={"captured_automatically": True},
            )
            return node

    def capture_thread(
        self,
        conversation_id: int,
        up_to_message_id: Optional[int] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        with get_connection() as conn:
            # Verify conversation exists first to prevent orphan nodes
            conv = conv_repo.get(conn, conversation_id)
            if not conv:
                raise ValueError(f"Conversation {conversation_id} does not exist")

            messages = message_repo.list_by_conversation(conn, conversation_id)
            if not messages:
                raise ValueError(f"No messages found for conversation {conversation_id}")

            target_msgs = []
            for msg in messages:
                target_msgs.append(msg)
                if up_to_message_id is not None and msg["id"] == up_to_message_id:
                    break
            if up_to_message_id is not None and not any(
                msg["id"] == up_to_message_id for msg in target_msgs
            ):
                raise ValueError(f"Message {up_to_message_id} not found in conversation {conversation_id}")

            conversation_title = (conv.get("title") or "Conversation").strip()
            base_title = title.strip() if title and title.strip() else f"{conversation_title} — saved thread"

            transcript = "\n\n".join(
                f"{msg['role'].capitalize()}:\n{msg['content']}" for msg in target_msgs
            )
            metadata = {
                "turn_count": len(target_msgs),
                "message_ids": [msg["id"] for msg in target_msgs],
                "thread_title": base_title,
            }
            existing = memory_graph_repo.list_nodes(conn, "thread_snapshot", conversation_id)
            if existing:
                # Keep the stable node id so user-created links survive a refresh.
                node = memory_graph_repo.update_node(
                    conn,
                    existing[0]["id"],
                    base_title,
                    transcript,
                    target_msgs[-1]["id"],
                    metadata,
                )
                for duplicate in existing[1:]:
                    memory_graph_repo.delete_node(conn, duplicate["id"])
            else:
                node = memory_graph_repo.create_node(
                    conn=conn,
                    node_id=f"mem_thr_{conversation_id}_{uuid.uuid4().hex[:8]}",
                    node_type="thread_snapshot",
                    title=base_title,
                    content=transcript,
                    source_conversation_id=conversation_id,
                    source_message_id=target_msgs[-1]["id"],
                    metadata=metadata,
                )

            return {
                "thread_title": base_title,
                "nodes": [node],
                "edges": [],
            }

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str = "relates_to",
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        with get_connection() as conn:
            if source_id == target_id:
                raise ValueError("A memory cannot be linked to itself")
            src = memory_graph_repo.get_node(conn, source_id)
            tgt = memory_graph_repo.get_node(conn, target_id)
            if not src or not tgt:
                raise ValueError("Both source and target nodes must exist")
            return memory_graph_repo.create_edge(conn, source_id, target_id, relation, metadata)

    def delete_node(self, node_id: str) -> bool:
        with get_connection() as conn:
            return memory_graph_repo.delete_node(conn, node_id)

    def delete_edge(self, edge_id: int) -> bool:
        with get_connection() as conn:
            return memory_graph_repo.delete_edge(conn, edge_id)

    def get_graph(
        self,
        node_type: Optional[str] = None,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        with get_connection() as conn:
            self._normalize_legacy_thread_snapshots(conn, conversation_id)
            return memory_graph_repo.get_graph(conn, node_type, conversation_id)

    def _normalize_legacy_thread_snapshots(
        self,
        conn,
        conversation_id: Optional[int] = None,
    ) -> None:
        """Collapse snapshots created by the old one-node-per-turn implementation."""
        nodes = memory_graph_repo.list_nodes(conn, "thread_snapshot", conversation_id)
        grouped = defaultdict(list)
        for node in nodes:
            if node.get("source_conversation_id") is not None:
                grouped[node["source_conversation_id"]].append(node)

        for source_id, snapshots in grouped.items():
            if len(snapshots) < 2:
                continue
            snapshots.sort(key=lambda node: node.get("metadata", {}).get("turn", 0))
            title = f"{snapshots[0].get('metadata', {}).get('thread_title') or f'Conversation {source_id}'} — saved thread"
            transcript = "\n\n".join(
                f"{node.get('metadata', {}).get('role', 'message').capitalize()}:\n{node['content']}"
                for node in snapshots
            )
            memory_graph_repo.delete_nodes(
                conn,
                node_type="thread_snapshot",
                conversation_id=source_id,
            )
            memory_graph_repo.create_node(
                conn,
                node_id=f"mem_thr_{source_id}_{uuid.uuid4().hex[:8]}",
                node_type="thread_snapshot",
                title=title,
                content=transcript,
                source_conversation_id=source_id,
                source_message_id=snapshots[-1].get("source_message_id"),
                metadata={
                    "turn_count": len(snapshots),
                    "message_ids": [
                        node.get("source_message_id")
                        for node in snapshots
                        if node.get("source_message_id") is not None
                    ],
                    "thread_title": title,
                },
            )

    def compile_context(
        self,
        conn,
        node_ids: List[str],
        depth: int = 1,
    ) -> str:
        if not node_ids:
            return ""
        subgraph = memory_graph_repo.get_subgraph(conn, node_ids, depth=depth)
        nodes = subgraph.get("nodes", [])
        edges = subgraph.get("edges", [])
        if not nodes:
            return ""

        node_map = {n["id"]: n for n in nodes}
        edge_map: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
        for e in edges:
            src_id = e["source_id"]
            tgt_id = e["target_id"]
            rel = e.get("relation", "relates_to")
            if src_id in edge_map and tgt_id in node_map:
                edge_map[src_id].append(f"{rel} -> {node_map[tgt_id].get('title') or tgt_id}")

        blocks = []
        for n in nodes:
            block = [
                f"### Memory: {n.get('title') or n['id']} (Type: {n.get('node_type', 'node')})",
                f"{n.get('content', '').strip()}",
            ]
            relations = edge_map.get(n["id"], [])
            if relations:
                block.append("Connected knowledge:")
                for r in relations:
                    block.append(f"  - {r}")
            blocks.append("\n".join(block))

        joined = "\n\n".join(blocks)
        return (
            "Relevant background memory graph context:\n"
            f"{joined}\n"
            "Use this memory context as factual reference when addressing the user's prompt."
        )


memory_graph_service = MemoryGraphService()
