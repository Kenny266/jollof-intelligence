"""
RAG pipeline — retrieves relevant context (user history + similar items)
from ChromaDB and assembles it into a prompt-ready string.
Metrics emitted per request per RAG observability standards.
"""
import logging
import time
from typing import Any, Optional

from shared.retrieval.vectorstore import search

logger = logging.getLogger(__name__)


def _item_display_name(item: dict[str, Any]) -> str:
    """Resolve item title from Chroma metadata or LLM output fields."""
    return (
        item.get("item_title")
        or item.get("title")
        or item.get("name")
        or "Unknown"
    )


def build_user_context(
    persona: dict[str, Any],
    query: str,
    top_k: int = 5,
    user_id: Optional[str] = None,
) -> tuple[str, dict[str, float]]:
    """
    Build a prompt-ready context string for Task A (user modeling).

    Returns:
        A tuple of (context_string, metrics_dict) where metrics_dict contains
        retrieval latency, hit rate, and result count for observability.
    """
    t0 = time.perf_counter()

    where_filter = {"user_id": user_id} if user_id else None
    retrieved = search(query, top_k=top_k, where=where_filter)

    retrieval_ms = (time.perf_counter() - t0) * 1000
    hit_rate = 1.0 if retrieved else 0.0

    logger.info(
        "RAG retrieval",
        extra={"user_id": user_id, "query": query[:80], "results": len(retrieved), "latency_ms": retrieval_ms},
    )

    lines = [
        "USER PROFILE:",
        f"  - Average rating given: {persona['avg_rating']} / 5",
        f"  - Rating variability (std): {persona.get('rating_std', 1.0):.2f}",
        f"  - Preferred categories: {', '.join(persona.get('top_categories', [])) or 'unknown'}",
        f"  - Review style: {persona.get('tone', 'concise')}, {persona.get('sentiment_tendency', 'balanced')}",
        f"  - Total reviews on record: {persona.get('review_count', 0)}",
        "",
    ]

    if persona.get("sample_reviews"):
        lines.append("SAMPLE PAST REVIEWS BY THIS USER:")
        for rev in persona["sample_reviews"][:3]:
            snippet = rev[:150].strip()
            if snippet:
                lines.append(f'  - "{snippet}..."')
        lines.append("")

    if retrieved:
        lines.append("RETRIEVED SIMILAR ITEMS FROM THE CATALOGUE:")
        for i, item in enumerate(retrieved, 1):
            name = _item_display_name(item)
            category = item.get("categories") or item.get("category") or "?"
            score = item.get("similarity_score", 0.0)
            lines.append(f"  {i}. {name} [{category}] — relevance {score:.2f}")
        lines.append("")

    metrics = {
        "retrieval_latency_ms": retrieval_ms,
        "retrieval_hit_rate": hit_rate,
        "retrieval_result_count": float(len(retrieved)),
    }
    return "\n".join(lines), metrics


def build_recommendation_context(
    persona: dict[str, Any],
    query: str,
    candidates: list[dict[str, Any]],
) -> str:
    """
    Build a prompt-ready context string for Task B (recommendation).
    Combines persona signals and pre-fetched candidate items.
    """
    lines = [
        "USER PROFILE:",
        f"  - Average rating: {persona['avg_rating']} / 5",
        f"  - Preferred categories: {', '.join(persona.get('top_categories', [])) or 'unknown'}",
        f"  - Review style: {persona.get('tone', 'concise')}, {persona.get('sentiment_tendency', 'balanced')}",
        f"  - Cold-start user: {'Yes' if persona.get('cold_start') else 'No'}",
        "",
        f"CURRENT REQUEST: \"{query}\"",
        "",
        "CANDIDATE ITEMS:",
    ]
    for i, item in enumerate(candidates, 1):
        name = _item_display_name(item)
        category = item.get("categories") or item.get("category") or "?"
        rating = item.get("average_rating") or item.get("rating") or "N/A"
        price = item.get("price", "N/A")
        score = item.get("similarity_score", 0.0)
        lines.append(
            f"  {i}. {name} | Category: {category} | Avg rating: {rating} | "
            f"Price: ${price} | Relevance: {score:.2f}"
        )

    return "\n".join(lines)
