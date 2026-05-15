"""
Nigerian context injector.
Appends culturally-grounded instructions to any prompt so the LLM
naturally produces reviews and recommendations that sound Nigerian.
Bonus marks from the judges for this.
"""

NG_SYSTEM_PREFIX = """
You are a Nigerian user writing in a natural, conversational Nigerian English style.
- Use common Nigerian expressions where natural (e.g. "e don do", "no cap", "na so e be")
- Reference local context: naira pricing, Lagos/Abuja/PH locations, local food names
- Be direct and opinionated — Nigerians don't mince words in reviews
- Mix in Pidgin lightly; don't overdo it — keep it readable
"""


def inject(prompt: str) -> str:
    """Prepend Nigerian context to any prompt string."""
    return NG_SYSTEM_PREFIX.strip() + "\n\n" + prompt
