"""
Review generator — builds prompt from persona + product context
and calls the shared LLM client to produce a review.
"""
from shared.llm.client import generate
from shared.llm.nigerian_context import inject
from shared.persona.builder import build_persona
from typing import Dict, Any


def load_prompt_template(path: str = "task_a/prompts/review_prompt.txt") -> str:
    with open(path) as f:
        return f.read()


def generate_review(persona: Dict[str, Any], product: Dict[str, Any], rating: int) -> str:
    template = load_prompt_template()
    prompt = template.format(
        avg_rating=persona["avg_rating"],
        tone=persona["tone"],
        sentiment=persona["sentiment_tendency"],
        top_categories=", ".join(persona["top_categories"]) or "various",
        sample_reviews="\n".join(f'- "{r}"' for r in persona["sample_reviews"][:2]),
        product_name=product.get("name", "this product"),
        product_category=product.get("category", "general"),
        product_location=product.get("location", ""),
        rating=rating,
    )
    prompt = inject(prompt)
    return generate(prompt, max_new_tokens=300)
