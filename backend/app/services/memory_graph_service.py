import uuid
from typing import Any, Dict, List, Optional

from app.infrastructure.db.connection import get_connection
from app.infrastructure.db.repositories import (
    ConversationRepository,
    MemoryGraphRepository,
    MessageRepository,
)

memory_graph_repo = MemoryGraphRepository()
message_repo = MessageRepository()
conv_repo = ConversationRepository()


class MemoryGraphService:
    """Service handling graph-based memory storage, thread capture, linking, and context assembly."""

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
            default_title = (
                title
                if title and title.strip()
                else f"Note from Chat #{conversation_id}: {target['content'][:35].strip()}..."
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

            base_title = title.strip() if title and title.strip() else f"Thread #{conversation_id} Snapshot"
            created_nodes = []
            created_edges = []
            prev_node_id = None

            for idx, msg in enumerate(target_msgs):
                node_id = f"mem_thr_{conversation_id}_msg_{msg['id']}_{uuid.uuid4().hex[:4]}"
                turn_title = f"{base_title} - Turn {idx + 1} ({msg['role']})"
                node = memory_graph_repo.create_node(
                    conn=conn,
                    node_id=node_id,
                    node_type="thread_snapshot",
                    title=turn_title,
                    content=msg["content"],
                    source_conversation_id=conversation_id,
                    source_message_id=msg["id"],
                    metadata={
                        "turn": idx + 1,
                        "role": msg["role"],
                        "model": msg.get("model"),
                        "thread_title": base_title,
                    },
                )
                created_nodes.append(node)

                if prev_node_id is not None:
                    edge = memory_graph_repo.create_edge(
                        conn=conn,
                        source_id=prev_node_id,
                        target_id=node_id,
                        relation="follows",
                        metadata={"turn_transition": f"{idx} -> {idx + 1}"},
                    )
                    created_edges.append(edge)
                prev_node_id = node_id

            return {
                "thread_title": base_title,
                "nodes": created_nodes,
                "edges": created_edges,
            }

    def create_edge(
        self,
        source_id: str,
        target_id: str,
        relation: str = "relates_to",
        metadata: Optional[dict] = None,
    ) -> Dict[str, Any]:
        with get_connection() as conn:
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
            return memory_graph_repo.get_graph(conn, node_type, conversation_id)

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
