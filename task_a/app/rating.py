"""
Rating predictor — estimates a 1-5 star rating from persona signals
before passing to the review generator. Keeps rating and text consistent.
"""
from typing import Dict, Any
import random


def predict_rating(persona: Dict[str, Any], product: Dict[str, Any]) -> int:
    """
    Heuristic + LLM-guided rating prediction.
    In production: fine-tune a regression head or prompt the LLM
    to output a rating first, then generate text conditioned on it.
    """
    base = persona.get("avg_rating", 3.5)
    std = persona.get("rating_std", 1.0)

    # Gaussian sample clipped to [1, 5]
    sampled = base + random.gauss(0, std * 0.5)
    rating = max(1, min(5, round(sampled)))
    return int(rating)
