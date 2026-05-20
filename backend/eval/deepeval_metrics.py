"""
DeepEval-based RAG metrics for both tasks.

Metrics computed:
  - Answer Relevancy     — does the output address the input query?
  - Faithfulness         — is the output grounded in the retrieved context?
  - Contextual Relevancy — is the retrieved context relevant to the query?
  - G-Eval               — general quality score via LLM-as-judge

DeepEval requires an LLM judge. We configure it to use the local Ollama
model so no external API keys are needed.

Usage:
    python -m eval.deepeval_metrics --preds preds.json --task a
"""
import logging

logger = logging.getLogger(__name__)


def _get_ollama_model():
    """
    Create a DeepEval-compatible Ollama LLM judge.

    Deliberately routes through ``generate_judge()`` which targets
    ``settings.judge_model`` (default: llama3.2:3b) rather than the
    generation model (deepseek-r1:1.5b) to prevent self-evaluation bias.
    """
    from deepeval.models.base_model import DeepEvalBaseLLM
    import asyncio
    from shared.llm.client import generate_judge

    class OllamaJudge(DeepEvalBaseLLM):
        def __init__(self):
            super().__init__()

        def load_model(self):
            return self

        def generate(self, prompt: str) -> str:
            return asyncio.get_event_loop().run_until_complete(
                generate_judge(prompt, max_tokens=512, temperature=0.0)
            )

        async def a_generate(self, prompt: str) -> str:
            return await generate_judge(prompt, max_tokens=512, temperature=0.0)

        def get_model_name(self) -> str:
            from src.config import get_settings
            return get_settings().judge_model

    return OllamaJudge()


def evaluate_rag_metrics(
    queries: list[str],
    retrieved_contexts: list[list[str]],
    actual_outputs: list[str],
    expected_outputs: list[str] | None = None,
) -> dict[str, float]:
    """
    Run DeepEval RAG metrics over a batch of predictions.

    Args:
        queries: Input queries / user requests.
        retrieved_contexts: Retrieved context chunks per query.
        actual_outputs: Generated outputs (reviews or recommendation reasons).
        expected_outputs: Optional reference outputs for reference-based metrics.

    Returns:
        Dict of mean metric scores.
    """
    from deepeval import evaluate
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        FaithfulnessMetric,
        ContextualRelevancyMetric,
        GEval,
    )
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams

    judge = _get_ollama_model()

    answer_rel = AnswerRelevancyMetric(threshold=0.5, model=judge, include_reason=True)
    faithfulness = FaithfulnessMetric(threshold=0.5, model=judge, include_reason=True)
    ctx_rel = ContextualRelevancyMetric(threshold=0.5, model=judge, include_reason=True)
    g_eval = GEval(
        name="Quality",
        criteria=(
            "Evaluate the quality and naturalness of the generated text. "
            "Does it sound authentic, relevant, and free of hallucinations?"
        ),
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=judge,
    )

    test_cases = []
    for i, (query, ctx, output) in enumerate(zip(queries, retrieved_contexts, actual_outputs)):
        tc = LLMTestCase(
            input=query,
            actual_output=output,
            retrieval_context=ctx,
            expected_output=expected_outputs[i] if expected_outputs else None,
        )
        test_cases.append(tc)

    results = evaluate(test_cases, [answer_rel, faithfulness, ctx_rel, g_eval])

    scores: dict[str, list[float]] = {
        "answer_relevancy": [],
        "faithfulness": [],
        "contextual_relevancy": [],
        "g_eval_quality": [],
    }
    for tc in results.test_results:
        for metric_result in tc.metrics_data:
            name = metric_result.name.lower().replace(" ", "_")
            if name in scores:
                scores[name].append(metric_result.score or 0.0)

    return {k: (sum(v) / len(v) if v else 0.0) for k, v in scores.items()}
