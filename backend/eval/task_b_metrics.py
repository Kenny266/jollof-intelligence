"""
Task B evaluation metrics: NDCG@K, Hit Rate@K, MRR.

Usage:
    from eval.task_b_metrics import evaluate_task_b
    results = evaluate_task_b(predictions, ground_truth, k=10)
"""
import logging
import math

logger = logging.getLogger(__name__)


def dcg(relevances: list[int], k: int = 10) -> float:
    return sum(
        rel / math.log2(i + 2)
        for i, rel in enumerate(relevances[:k])
    )


def ndcg(pred_ids: list[str], true_ids: set[str], k: int = 10) -> float:
    relevances = [1 if pid in true_ids else 0 for pid in pred_ids[:k]]
    ideal = sorted(relevances, reverse=True)
    idcg = dcg(ideal, k)
    return dcg(relevances, k) / idcg if idcg > 0 else 0.0


def hit_rate(pred_ids: list[str], true_ids: set[str], k: int = 10) -> float:
    return 1.0 if any(pid in true_ids for pid in pred_ids[:k]) else 0.0


def mrr(pred_ids: list[str], true_ids: set[str]) -> float:
    """Mean Reciprocal Rank — reciprocal of the rank of the first relevant item."""
    for i, pid in enumerate(pred_ids, 1):
        if pid in true_ids:
            return 1.0 / i
    return 0.0


def evaluate_task_b(
    predictions: list[dict],
    ground_truth: list[dict],
    k: int = 10,
) -> dict[str, float]:
    """
    Full Task B evaluation.

    Args:
        predictions: List of dicts, each with key 'recommendations': list of
                     dicts with 'item_id' key.
        ground_truth: List of dicts, each with key 'relevant_items': list of item IDs.
        k: Cutoff rank for NDCG and Hit Rate.

    Returns:
        Dict of NDCG@k, HitRate@k, MRR scores.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")

    ndcg_scores, hr_scores, mrr_scores = [], [], []

    for pred, truth in zip(predictions, ground_truth):
        pred_ids = [r.get("item_id", "") for r in pred.get("recommendations", [])]
        true_ids = set(truth.get("relevant_items", []))
        ndcg_scores.append(ndcg(pred_ids, true_ids, k))
        hr_scores.append(hit_rate(pred_ids, true_ids, k))
        mrr_scores.append(mrr(pred_ids, true_ids))

    return {
        f"ndcg_at_{k}": sum(ndcg_scores) / len(ndcg_scores),
        f"hit_rate_at_{k}": sum(hr_scores) / len(hr_scores),
        "mrr": sum(mrr_scores) / len(mrr_scores),
    }
