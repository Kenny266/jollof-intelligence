"""
RAG pipeline — retrieves relevant context (user history + similar items)
and assembles it into a prompt-ready string.
"""
from typing import List, Dict, Any
from shared.retrieval.vectorstore import search


def build_context(persona: Dict[str, Any], query: str, top_k: int = 5) -> str:
    """
    Combine persona signals and retrieved items into a context string
    that gets injected into the LLM prompt.
    """
    retrieved = search(query, top_k=top_k)

    lines = [
        f"User profile:",
        f"  - Avg rating: {persona['avg_rating']} / 5",
        f"  - Preferred categories: {', '.join(persona['top_categories']) or 'unknown'}",
        f"  - Review style: {persona['tone']}, {persona['sentiment_tendency']}",
        "",
        "Similar items from our catalogue:",
    ]
    for i, item in enumerate(retrieved, 1):
        lines.append(f"  {i}. {item.get('name','?')} ({item.get('category','?')}) — score {item['similarity_score']:.2f}")

    if persona.get("sample_reviews"):
        lines += ["", "Sample of this user's past reviews:"]
        for rev in persona["sample_reviews"][:2]:
            lines.append(f'  "{rev[:120]}..."')

    return "\n".join(lines)
