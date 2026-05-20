"""
Async Ollama HTTP client.
Both Task A and Task B agents import `generate()` from here so the
connection is reused across requests.
"""
import asyncio
import json
import logging
import re
from typing import Optional

import httpx

from src.config import get_settings

logger = logging.getLogger(__name__)


async def generate(
    prompt: str,
    system: str = "",
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    think: Optional[bool] = None,
) -> str:
    """
    Send a generation request to the local Ollama server.

    Args:
        prompt: The user-facing prompt text.
        system: Optional system-level instructions (injected separately by Ollama).
        max_tokens: Override the default max new tokens from settings.
        temperature: Override the default temperature from settings.
        think: Qwen3 thinking mode. False → /no_think (fast, fluent). True → /think
               (chain-of-thought). None → model default.

    Returns:
        The stripped response text from the model.

    Raises:
        RuntimeError: When the Ollama server is unreachable or returns an error.
    """
    settings = get_settings()
    options: dict[str, object] = {
        "temperature": temperature if temperature is not None else settings.llm_temperature,
        "top_p": settings.llm_top_p,
        "num_predict": max_tokens if max_tokens is not None else settings.llm_max_tokens,
    }

    payload: dict[str, object] = {
        "model": settings.agent_model,
        "prompt": prompt,
        "stream": False,
        "options": options,
    }
    if system:
        payload["system"] = system
    # Qwen3 thinking mode: top-level field, NOT inside options.
    # Passing it inside options causes Ollama to log "invalid option provided option=think".
    if think is not None:
        payload["think"] = think

    url = f"{settings.ollama_base_url}/api/generate"
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                text = data.get("response", "").strip()
                # Strip chain-of-thought blocks emitted by Qwen3/DeepSeek when think=True
                text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
                return text
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Ollama returned HTTP error",
                extra={"status_code": exc.response.status_code, "url": url, "attempt": attempt + 1},
            )
            raise RuntimeError(f"Ollama HTTP error {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            last_exc = exc
            if attempt < 2:
                wait = 2 ** attempt
                logger.warning(
                    "Ollama unreachable (attempt %d/3), retrying in %ds: %s",
                    attempt + 1, wait, exc,
                )
                await asyncio.sleep(wait)
            else:
                logger.error("Ollama request failed after 3 attempts", extra={"url": url, "error": str(exc)})
    raise RuntimeError(f"Cannot reach Ollama at {url}") from last_exc


async def generate_judge(
    prompt: str,
    max_tokens: Optional[int] = 512,
    temperature: Optional[float] = 0.0,
) -> str:
    """
    Send a generation request using the dedicated judge model.

    Uses ``settings.judge_model`` instead of ``settings.agent_model`` so that
    evaluation never grades the same model that produced the output, avoiding
    self-evaluation bias.

    Args:
        prompt: The evaluation prompt to send to the judge.
        max_tokens: Max tokens for the judge response (default 512).
        temperature: Sampling temperature for the judge (default 0.0 for
                     deterministic scoring).

    Returns:
        The stripped response text from the judge model.

    Raises:
        RuntimeError: When the Ollama server is unreachable or returns an error.
    """
    settings = get_settings()
    payload = {
        "model": settings.judge_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": settings.llm_top_p,
            "num_predict": max_tokens,
        },
    }

    url = f"{settings.ollama_judge_url}/api/generate"
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "").strip()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Ollama judge returned HTTP error",
            extra={"status_code": exc.response.status_code, "url": url},
        )
        raise RuntimeError(f"Ollama judge HTTP error {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        logger.error("Ollama judge request failed", extra={"url": url, "error": str(exc)})
        raise RuntimeError(f"Cannot reach Ollama judge at {url}") from exc


def extract_json_block(text: str) -> dict[str, object]:
    """
    Attempt to extract a JSON object from LLM output that may contain
    markdown fences, reasoning preamble, or trailing text.

    Raises:
        ValueError: If no valid JSON object is found.
    """
    # Strip reasoning blocks (<think>...</think>) emitted by DeepSeek-R1 and Qwen3
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    # Strip markdown code fences
    text = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()

    # Try to find the first {...} block
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM output: {text[:200]!r}")
    try:
        return json.loads(match.group())
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in LLM output: {match.group()[:200]!r}") from exc
