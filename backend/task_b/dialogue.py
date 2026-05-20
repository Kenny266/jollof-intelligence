"""
Multi-turn dialogue manager for Task B.

Maintains conversation history and generates follow-up questions
to progressively refine recommendations over multiple turns.
"""
import logging
import re
from typing import Any

from shared.llm.client import generate
from shared.llm.nigerian_context import get_system_prompt

logger = logging.getLogger(__name__)

FOLLOW_UP_PROMPT = """
You are a helpful Nigerian book recommendation assistant.

The user asked: "{user_request}"
You recommended: {item_names}

Generate ONE short, natural follow-up question in Nigerian English to refine
the recommendations further. Examples:
  "Are you looking for something you can finish in a weekend?"
  "You prefer the physical book or e-book, abeg?"
  "Is this for relaxation or you want something that will challenge you?"

One sentence only. No preamble.
"""

REFINED_QUERY_PROMPT = """
Conversation so far:
{conversation_history}

Latest user message: "{latest_message}"

Based on this conversation, generate an optimized semantic search query
that captures what the user wants next (1-2 sentences max).
Return ONLY the query string, nothing else.
"""


def _strip_think_blocks(text: str) -> str:
    """Remove <think>...</think> blocks so reasoning traces don't pollute context."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def format_conversation(turns: list[dict[str, str]]) -> str:
    """Format conversation turns into a readable string for prompt injection.

    Assistant turns are stripped of any <think> blocks before injection to
    prevent reasoning traces from filling the context window.
    """
    lines = []
    for turn in turns:
        role = turn.get("role", "")
        content = turn.get("content", "").strip()
        if role != "user":
            content = _strip_think_blocks(content)
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {content}")
    return "\n".join(lines)


async def generate_follow_up(
    user_request: str,
    recommendations: list[dict[str, Any]],
) -> str:
    """
    Generate a single follow-up question to refine recommendations.

    Args:
        user_request: The user's original request text.
        recommendations: List of recommendation dicts (with 'title' key).

    Returns:
        A follow-up question string.
    """
    item_names = ", ".join(
        r.get("title") or r.get("name", "") for r in recommendations[:3]
    )
    prompt = FOLLOW_UP_PROMPT.format(user_request=user_request, item_names=item_names)
    try:
        follow_up = await generate(
            prompt,
            system=get_system_prompt(),
            max_tokens=80,
            temperature=0.7,
            think=False,
        )
        return follow_up.strip().strip('"')
    except Exception as exc:
        logger.warning("Follow-up generation failed: %s", exc)
        return "What kind of book are you in the mood for — something fun or something deep?"


async def refine_query_from_conversation(
    conversation: list[dict[str, str]],
    latest_message: str,
) -> str:
    """
    Use conversation history to generate a refined semantic search query
    for the next retrieval round.
    """
    if not conversation:
        return latest_message

    history_str = format_conversation(conversation)
    prompt = REFINED_QUERY_PROMPT.format(
        conversation_history=history_str,
        latest_message=latest_message,
    )
    try:
        refined = await generate(prompt, max_tokens=100, temperature=0.3, think=True)
        return refined.strip()
    except Exception as exc:
        logger.warning("Query refinement failed: %s — using original", exc)
        return latest_message
