"""
Persona builder — converts a user's review history into a structured
profile dict that both Task A and Task B agents consume.
"""
from collections import Counter
from typing import List, Dict, Any


def build_persona(user_id: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Args:
        user_id: unique user identifier
        history: list of past review dicts, each with keys:
                 item_name, category, rating (1-5), review_text, date

    Returns:
        persona dict with derived behavioural signals
    """
    if not history:
        return _cold_start_persona(user_id)

    ratings = [r["rating"] for r in history]
    categories = [r.get("category", "unknown") for r in history]
    avg_rating = sum(ratings) / len(ratings)
    rating_std = (sum((r - avg_rating) ** 2 for r in ratings) / len(ratings)) ** 0.5

    top_categories = [cat for cat, _ in Counter(categories).most_common(3)]

    # Tone signal: are they verbose or terse?
    avg_review_len = sum(len(r.get("review_text", "").split()) for r in history) / len(history)
    tone = "detailed" if avg_review_len > 50 else "concise"

    # Sentiment tendency
    positivity = sum(1 for r in ratings if r >= 4) / len(ratings)
    sentiment_tendency = "positive" if positivity > 0.6 else "critical" if positivity < 0.3 else "balanced"

    return {
        "user_id": user_id,
        "avg_rating": round(avg_rating, 2),
        "rating_std": round(rating_std, 2),
        "top_categories": top_categories,
        "tone": tone,
        "sentiment_tendency": sentiment_tendency,
        "review_count": len(history),
        "sample_reviews": [r.get("review_text", "") for r in history[:3]],
    }


def _cold_start_persona(user_id: str) -> Dict[str, Any]:
    """Fallback persona for users with no history."""
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
