"""
Multi-turn dialogue manager for Task B.
Maintains conversation context and generates follow-up questions
to refine recommendations.
"""
from shared.llm.client import generate
from shared.llm.nigerian_context import inject
from typing import List, Dict

FOLLOW_UP_PROMPT = """
You are a helpful Nigerian recommendation assistant.
The user asked: "{user_context}"
You recommended: {item_names}

Generate ONE short, natural follow-up question to refine the recommendations further.
Examples: "Are you looking for something budget-friendly?" / "Do you prefer indoor or outdoor?"
One sentence only.
"""


def generate_follow_up(context: str, recommendations: List[Dict]) -> str:
    item_names = ", ".join(r.get("name", "") for r in recommendations[:3])
    prompt = FOLLOW_UP_PROMPT.format(user_context=context, item_names=item_names)
    prompt = inject(prompt)
    return generate(prompt, max_new_tokens=80).strip()


def format_conversation_history(turns: List[Dict]) -> str:
    lines = []
    for turn in turns:
        role = "User" if turn["role"] == "user" else "Assistant"
        lines.append(f"{role}: {turn['content']}")
    return "\n".join(lines)
