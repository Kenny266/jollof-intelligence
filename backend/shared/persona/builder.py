"""
Persona builder — converts a user's review history into a structured
profile dict that both Task A and Task B agents consume.
"""
import math
from collections import Counter
from typing import Any


def build_persona(user_id: str, history: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Derive behavioural signals from a user's review history.

    Args:
        user_id: Unique user identifier.
        history: List of past review dicts, each with keys:
                 item_name, category, rating (1-5), review_text, date (optional).

    Returns:
        Persona dict with derived behavioural signals.
        Includes 'cold_start: True' when history is absent.
    """
    if not history:
        return _cold_start_persona(user_id)

    ratings = [float(r.get("rating", 3)) for r in history]
    categories = [r.get("category", "unknown") for r in history]

    avg_rating = sum(ratings) / len(ratings)
    variance = sum((r - avg_rating) ** 2 for r in ratings) / len(ratings)
    rating_std = math.sqrt(variance)

    top_categories = [cat for cat, _ in Counter(categories).most_common(3)]

    avg_review_len = (
        sum(len(r.get("review_text", "").split()) for r in history) / len(history)
    )
    tone = "detailed" if avg_review_len > 50 else "concise"

    positivity = sum(1 for r in ratings if r >= 4) / len(ratings)
    if positivity > 0.6:
        sentiment_tendency = "positive"
    elif positivity < 0.3:
        sentiment_tendency = "critical"
    else:
        sentiment_tendency = "balanced"

    # Recency bias: weight more recent reviews higher for sample selection
    sorted_history = sorted(history, key=lambda r: r.get("date") or "", reverse=True)
    sample_reviews = [
        r.get("review_text", "").strip()
        for r in sorted_history[:5]
        if r.get("review_text", "").strip()
    ]

    return {
        "user_id": user_id,
        "avg_rating": round(avg_rating, 2),
        "rating_std": round(rating_std, 2),
        "top_categories": top_categories,
        "tone": tone,
        "sentiment_tendency": sentiment_tendency,
        "review_count": len(history),
        "sample_reviews": sample_reviews,
        "cold_start": False,
    }


def _cold_start_persona(user_id: str) -> dict[str, Any]:
    """
    Fallback persona for users with no review history.
    The 'cold_start' flag routes Task B through the cold-start agent path.
    """
    return {
        "user_id": user_id,
        "avg_rating": 3.5,
        "rating_std": 1.0,
        "top_categories": [],
        "tone": "concise",
        "sentiment_tendency": "balanced",
        "review_count": 0,
        "sample_reviews": [],
        "cold_start": True,
    }
