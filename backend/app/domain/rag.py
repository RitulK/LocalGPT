from typing import Any, Dict, List


def public_sources(sources: List[Any]) -> List[Dict[str, Any]]:
    result = []
    for idx, source in enumerate(sources, start=1):
        if hasattr(source, "page_content"):
            meta = getattr(source, "metadata", {}) or {}
            content = source.page_content
        else:
            meta = source or {}
            content = source.get("content", "")

        page_no = meta.get("page_number")
        if page_no == -1:
            page_no = None

        normalized = " ".join(str(content).split()).strip()
        snippet = (
            normalized
            if len(normalized) <= 280
            else f"{normalized[:280].rstrip()}..."
        )

        result.append(
            {
                "source_index": meta.get("source_index", idx),
                "document_id": meta.get("document_id"),
                "filename": meta.get("filename", "Document"),
                "chunk_index": meta.get("chunk_index"),
                "page_number": page_no,
                "distance": meta.get("distance"),
                "snippet": snippet,
            }
        )
    return result


def format_rag_context(sources: List[Any]) -> str:
    context_blocks = []
    for idx, source in enumerate(sources, start=1):
        if hasattr(source, "page_content"):
            meta = getattr(source, "metadata", {}) or {}
            content = source.page_content
        else:
            meta = source or {}
            content = source.get("content", "")

        filename = meta.get("filename", "Document")
        page_no = meta.get("page_number")
        page = f", page {page_no}" if page_no and page_no != -1 else ""
        context_blocks.append(f"[{idx}] {filename}{page}\n{content}")

    return "\n\n".join(context_blocks)
