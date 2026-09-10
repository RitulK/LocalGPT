from typing import List


def public_sources(sources: List[dict]) -> List[dict]:
    return [
        {
            "source_index": source["source_index"],
            "document_id": source["document_id"],
            "filename": source["filename"],
            "chunk_index": source["chunk_index"],
            "page_number": source["page_number"],
            "distance": source["distance"],
            "snippet": source["snippet"],
        }
        for source in sources
    ]


def format_rag_context(sources: List[dict]) -> str:
    context_blocks = []
    for source in sources:
        page = f", page {source['page_number']}" if source.get("page_number") else ""
        context_blocks.append(
            f"[{source['source_index']}] {source['filename']}{page}\n"
            f"{source['content']}"
        )
    return "\n\n".join(context_blocks)
