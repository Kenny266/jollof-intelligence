"""
Task A evaluation script.
Metrics: ROUGE-L, BERTScore, RMSE on star ratings.

Usage:
    python -m task_a.eval.evaluate --predictions preds.json --references refs.json
"""
import argparse
import json
import math
from rouge_score import rouge_scorer
from bert_score import score as bert_score


def rmse(pred_ratings, true_ratings):
    n = len(pred_ratings)
    return math.sqrt(sum((p - t) ** 2 for p, t in zip(pred_ratings, true_ratings)) / n)


def evaluate(predictions_path: str, references_path: str):
    with open(predictions_path) as f:
        preds = json.load(f)
    with open(references_path) as f:
        refs = json.load(f)

    pred_texts = [p["review"] for p in preds]
    ref_texts = [r["review"] for r in refs]
    pred_ratings = [p["rating"] for p in preds]
    ref_ratings = [r["rating"] for r in refs]

    # ROUGE-L
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    rouge_scores = [scorer.score(ref, pred)["rougeL"].fmeasure for pred, ref in zip(pred_texts, ref_texts)]
    avg_rouge = sum(rouge_scores) / len(rouge_scores)

    # BERTScore
    P, R, F1 = bert_score(pred_texts, ref_texts, lang="en", verbose=False)
    avg_bertscore = F1.mean().item()

    # RMSE
    rating_rmse = rmse(pred_ratings, ref_ratings)

    print(f"ROUGE-L:    {avg_rouge:.4f}")
    print(f"BERTScore:  {avg_bertscore:.4f}")
    print(f"RMSE:       {rating_rmse:.4f}")

    return {
        "rouge_l": avg_rouge,
        "bert_score": avg_bertscore,
        "rmse": rating_rmse,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--predictions", required=True)
    parser.add_argument("--references", required=True)
    args = parser.parse_args()
    evaluate(args.predictions, args.references)
