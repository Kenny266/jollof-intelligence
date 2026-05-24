"""
Compute Task B metrics on cold-start vs warm subsets.

Expects each prediction dict to include an optional ``cold_start`` boolean flag.
"""
import logging

from eval.task_b_metrics import evaluate_task_b

logger = logging.getLogger(__name__)


def evaluate_task_b_subsets(
    predictions: list[dict],
    ground_truth: list[dict],
    k: int = 10,
) -> dict[str, float]:
    """Return NDCG/HitRate/MRR split by cold_start flag."""
    cold_preds: list[dict] = []
    cold_refs: list[dict] = []
    warm_preds: list[dict] = []
    warm_refs: list[dict] = []

    for pred, ref in zip(predictions, ground_truth):
        if pred.get("cold_start"):
            cold_preds.append(pred)
            cold_refs.append(ref)
        else:
            warm_preds.append(pred)
            warm_refs.append(ref)

    metrics: dict[str, float] = {}

    if cold_preds:
        cold = evaluate_task_b(cold_preds, cold_refs, k=k)
        metrics.update({f"cold_start_{name}": value for name, value in cold.items()})
        logger.info("Cold-start subset: %d examples", len(cold_preds))
    else:
        logger.info("No cold-start examples in prediction set")

    if warm_preds:
        warm = evaluate_task_b(warm_preds, warm_refs, k=k)
        metrics.update({f"warm_{name}": value for name, value in warm.items()})
        logger.info("Warm subset: %d examples", len(warm_preds))
    else:
        logger.info("No warm examples in prediction set")

    return metrics
