"""
Task B evaluation script.
Metrics: NDCG@10, Hit Rate@10

Usage:
    python -m task_b.eval.evaluate --predictions preds.json --ground_truth gt.json
"""
import argparse
import json
import math


def dcg(relevances: list, k: int = 10) -> float:
    return sum(
        rel / math.log2(i + 2)
        for i, rel in enumerate(relevances[:k])
    )


def ndcg(pred_ids: list, true_ids: set, k: int = 10) -> float:
    relevances = [1 if pid in true_ids else 0 for pid in pred_ids[:k]]
    ideal = sorted(relevances, reverse=True)
    idcg = dcg(ideal, k)
    return dcg(relevances, k) / idcg if idcg > 0 else 0.0


def hit_rate(pred_ids: list, true_ids: set, k: int = 10) -> float:
    return 1.0 if any(pid in true_ids for pid in pred_ids[:k]) else 0.0


def evaluate(predictions_path: str, ground_truth_path: str, k: int = 10):
    with open(predictions_path) as f:
        preds = json.load(f)
    with open(ground_truth_path) as f:
        gt = json.load(f)

    ndcg_scores, hr_scores = [], []

    for pred, truth in zip(preds, gt):
        pred_ids = [r["item_id"] for r in pred.get("recommendations", [])]
        true_ids = set(truth.get("relevant_items", []))
        ndcg_scores.append(ndcg(pred_ids, true_ids, k))
        hr_scores.append(hit_rate(pred_ids, true_ids, k))

    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores)
    avg_hr = sum(hr_scores) / len(hr_scores)

    print(f"NDCG@{k}:     {avg_ndcg:.4f}")
    print(f"HitRate@{k}:  {avg_hr:.4f}")
    return {"ndcg": avg_ndcg, "hit_rate": avg_hr}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--ground_truth", required=True)
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args()
    evaluate(args.predictions, args.ground_truth, args.k)
