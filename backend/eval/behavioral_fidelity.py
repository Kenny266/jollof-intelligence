"""
Behavioural fidelity evaluation — LLM-as-judge.

Scores:
  1. Persona Match (0-10): Does the simulated review match the user's authentic voice?
  2. Nigerian Persona Score (0-10): Does the output contain authentic Nigerian English markers?

These correspond to the 'Behavioural Fidelity (human eval)' and the
'contextualised to behave and sound like Nigerians' bonus in the rubric.
"""
import asyncio
import logging
import re
from typing import Any

from src.config import get_settings
from shared.llm.client import generate_judge, extract_json_block

logger = logging.getLogger(__name__)

PERSONA_MATCH_PROMPT = """
You are evaluating how well a simulated review matches a user's authentic writing voice.

USER'S REAL PAST REVIEWS:
{real_reviews}

SIMULATED REVIEW:
"{simulated_review}"

Score the simulated review on:
1. Voice Match (0-10): Does it sound like the same person? Same vocabulary level, sentence
   structure, emotional tone, and level of detail?
2. Consistency (0-10): Is the rating/sentiment consistent with the user's historical patterns?

Return ONLY this JSON:
{{
  "voice_match": <0-10>,
  "consistency": <0-10>,
  "reasoning": "<1 sentence explanation>"
}}
"""

NIGERIAN_PERSONA_PROMPT = """
You are evaluating whether the following text sounds authentically Nigerian.

TEXT:
"{text}"

Score on these dimensions:
1. Nigerian English authenticity (0-10): Natural use of Nigerian English patterns,
   expressions, and Pidgin (not forced, not excessive).
2. Cultural specificity (0-10): References to Nigerian context, values, pricing,
   or cultural touchpoints where appropriate.

Return ONLY this JSON:
{{
  "nigerian_english": <0-10>,
  "cultural_specificity": <0-10>,
  "reasoning": "<1 sentence explanation>"
}}
"""


async def score_persona_match(
    real_reviews: list[str],
    simulated_review: str,
) -> dict[str, Any]:
    """
    LLM-as-judge: score how well the simulated review matches the user's real voice.
    """
    real_block = "\n".join(f'  - "{r[:200]}"' for r in real_reviews[:3])
    prompt = PERSONA_MATCH_PROMPT.format(
        real_reviews=real_block,
        simulated_review=simulated_review[:400],
    )
    try:
        raw = await generate_judge(prompt, max_tokens=200, temperature=get_settings().llm_temperature)
        data = extract_json_block(raw)
        return {
            "voice_match": float(data.get("voice_match", 0)),
            "consistency": float(data.get("consistency", 0)),
            "reasoning": str(data.get("reasoning", "")),
        }
    except Exception as exc:
        logger.warning("Persona match scoring failed: %s", exc)
        return {"voice_match": 0.0, "consistency": 0.0, "reasoning": "scoring failed"}


async def score_nigerian_persona(text: str) -> dict[str, Any]:
    """
    LLM-as-judge: score how authentically Nigerian the text sounds.
    """
    prompt = NIGERIAN_PERSONA_PROMPT.format(text=text[:400])
    try:
        raw = await generate_judge(prompt, max_tokens=200, temperature=get_settings().llm_temperature)
        data = extract_json_block(raw)
        return {
            "nigerian_english": float(data.get("nigerian_english", 0)),
            "cultural_specificity": float(data.get("cultural_specificity", 0)),
            "reasoning": str(data.get("reasoning", "")),
        }
    except Exception as exc:
        logger.warning("Nigerian persona scoring failed: %s", exc)
        return {"nigerian_english": 0.0, "cultural_specificity": 0.0, "reasoning": "scoring failed"}


async def evaluate_behavioral_fidelity(
    predictions: list[dict],
) -> dict[str, float]:
    """
    Batch evaluation of behavioural fidelity across a prediction set.

    Args:
        predictions: List of dicts with keys:
                     - 'review': generated review text
                     - 'real_reviews': list of user's real past reviews (optional)

    Returns:
        Dict of mean scores.
    """
    tasks_persona = [
        score_persona_match(
            p.get("real_reviews", []),
            p.get("review", ""),
        )
        for p in predictions
        if p.get("real_reviews")
    ]
    tasks_ng = [
        score_nigerian_persona(p.get("review", ""))
        for p in predictions
    ]

    persona_results = await asyncio.gather(*tasks_persona)
    ng_results = await asyncio.gather(*tasks_ng)

    def mean(values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0

    return {
        "persona_voice_match": mean([r["voice_match"] for r in persona_results]),
        "persona_consistency": mean([r["consistency"] for r in persona_results]),
        "nigerian_english_score": mean([r["nigerian_english"] for r in ng_results]),
        "cultural_specificity_score": mean([r["cultural_specificity"] for r in ng_results]),
    }
