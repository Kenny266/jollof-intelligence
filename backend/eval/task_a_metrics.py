"""
Task A evaluation metrics: ROUGE, BERTScore, BLEU, RMSE.

Usage:
    from eval.task_a_metrics import evaluate_task_a
    results = evaluate_task_a(predictions, references)
"""
import logging
import math

logger = logging.getLogger(__name__)


def rmse(pred_ratings: list[float], true_ratings: list[float]) -> float:
    if len(pred_ratings) != len(true_ratings):
        raise ValueError("Prediction and reference lists must have the same length")
    n = len(pred_ratings)
    return math.sqrt(sum((p - t) ** 2 for p, t in zip(pred_ratings, true_ratings)) / n)


def compute_rouge(pred_texts: list[str], ref_texts: list[str]) -> dict[str, float]:
    """Compute ROUGE-1, ROUGE-2, ROUGE-L F1 scores."""
    from rouge_score import rouge_scorer as rs

    scorer = rs.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    r1, r2, rl = [], [], []
    for pred, ref in zip(pred_texts, ref_texts):
        scores = scorer.score(ref, pred)
        r1.append(scores["rouge1"].fmeasure)
        r2.append(scores["rouge2"].fmeasure)
        rl.append(scores["rougeL"].fmeasure)
    return {
        "rouge1": sum(r1) / len(r1),
        "rouge2": sum(r2) / len(r2),
        "rougeL": sum(rl) / len(rl),
    }


def compute_bertscore(pred_texts: list[str], ref_texts: list[str]) -> float:
    """Compute mean BERTScore F1."""
    from bert_score import score as bert_score

    _, _, F1 = bert_score(pred_texts, ref_texts, lang="en", verbose=False)
    return F1.mean().item()


def compute_bleu(pred_texts: list[str], ref_texts: list[str]) -> float:
    """Compute corpus-level BLEU using sacrebleu."""
    import sacrebleu

    refs = [[r] for r in ref_texts]
    result = sacrebleu.corpus_bleu(pred_texts, list(zip(*refs)))
    return result.score / 100.0


def evaluate_task_a(
    predictions: list[dict],
    references: list[dict],
) -> dict[str, float]:
    """
    Full Task A evaluation.

    Args:
        predictions: List of dicts with keys 'rating' (int) and 'review' (str).
        references: List of dicts with keys 'rating' (int) and 'review' (str).

    Returns:
        Dict of all metric scores.
    """
    if len(predictions) != len(references):
        raise ValueError("Predictions and references must have same length")

    pred_texts = [str(p.get("review", "")) for p in predictions]
    ref_texts = [str(r.get("review", "")) for r in references]
    pred_ratings = [float(p.get("rating", 3)) for p in predictions]
    ref_ratings = [float(r.get("rating", 3)) for r in references]

    logger.info("Computing ROUGE…")
    rouge = compute_rouge(pred_texts, ref_texts)

    logger.info("Computing BERTScore…")
    bert = compute_bertscore(pred_texts, ref_texts)

    logger.info("Computing BLEU…")
    bleu = compute_bleu(pred_texts, ref_texts)

    logger.info("Computing RMSE…")
    rating_rmse = rmse(pred_ratings, ref_ratings)

    results = {
        **rouge,
        "bert_score_f1": bert,
        "bleu": bleu,
        "rmse": rating_rmse,
    }
    return results
