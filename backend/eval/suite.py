"""
Unified evaluation runner for both tasks.

Usage:
    # Task A
    python -m eval.suite --task a --preds data/processed/task_a_preds.json \
                         --refs data/processed/task_a_refs.json

    # Task B
    python -m eval.suite --task b --preds data/processed/task_b_preds.json \
                         --refs data/processed/task_b_gt.json --k 10

    # Include DeepEval RAG metrics (requires Ollama running)
    python -m eval.suite --task a --preds ... --refs ... --deepeval

    # Include behavioural fidelity (requires Ollama running)
    python -m eval.suite --task a --preds ... --refs ... --fidelity
"""
import argparse
import asyncio
import json
import logging
import sys

from eval.generate_report import generate_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def load_json(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_task_a(preds: list[dict], refs: list[dict], deepeval: bool, fidelity: bool) -> dict:
    from eval.task_a_metrics import evaluate_task_a
    logger.info("Running Task A standard metrics…")
    metrics = evaluate_task_a(preds, refs)

    if fidelity:
        logger.info("Running behavioural fidelity evaluation…")
        from eval.behavioral_fidelity import evaluate_behavioral_fidelity
        # Attach real reviews from refs to preds for persona matching
        enriched = [
            {**p, "real_reviews": [refs[i].get("review", "")] if i < len(refs) else []}
            for i, p in enumerate(preds)
        ]
        fid = asyncio.run(evaluate_behavioral_fidelity(enriched))
        metrics.update(fid)

    if deepeval:
        logger.info("Running DeepEval RAG metrics…")
        from eval.deepeval_metrics import evaluate_rag_metrics
        queries = [p.get("product_title", "") for p in preds]
        contexts = [p.get("retrieved_context", [""])  for p in preds]
        outputs = [p.get("review", "") for p in preds]
        expected = [r.get("review", "") for r in refs]
        de = evaluate_rag_metrics(queries, contexts, outputs, expected)
        metrics.update(de)

    return metrics


def run_task_b(preds: list[dict], refs: list[dict], k: int, deepeval: bool) -> dict:
    from eval.task_b_metrics import evaluate_task_b
    from eval.task_b_subsets import evaluate_task_b_subsets
    logger.info("Running Task B standard metrics (k=%d)…", k)
    metrics = evaluate_task_b(preds, refs, k=k)

    subset_metrics = evaluate_task_b_subsets(preds, refs, k=k)
    metrics.update(subset_metrics)

    if deepeval:
        logger.info("Running DeepEval RAG metrics for Task B…")
        from eval.deepeval_metrics import evaluate_rag_metrics
        queries = [p.get("context", "") for p in preds]
        contexts = [p.get("retrieved_context", [""]) for p in preds]
        outputs = [
            " | ".join(r.get("reason", "") for r in p.get("recommendations", []))
            for p in preds
        ]
        de = evaluate_rag_metrics(queries, contexts, outputs)
        metrics.update(de)

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Jollof Intelligence Evaluation Suite")
    parser.add_argument("--task", required=True, choices=["a", "b"], help="Task to evaluate")
    parser.add_argument("--preds", required=True, help="Path to predictions JSON file")
    parser.add_argument("--refs", required=True, help="Path to references/ground truth JSON file")
    parser.add_argument("--k", type=int, default=10, help="Cutoff for Task B ranking metrics")
    parser.add_argument("--deepeval", action="store_true", help="Run DeepEval RAG metrics")
    parser.add_argument("--fidelity", action="store_true", help="Run behavioural fidelity metrics (Task A)")
    parser.add_argument("--output-dir", default="data/eval/reports", help="Directory for report output")
    args = parser.parse_args()

    preds = load_json(args.preds)
    refs = load_json(args.refs)
    logger.info("Loaded %d predictions and %d references", len(preds), len(refs))

    if args.task == "a":
        metrics = run_task_a(preds, refs, deepeval=args.deepeval, fidelity=args.fidelity)
    else:
        metrics = run_task_b(preds, refs, k=args.k, deepeval=args.deepeval)

    print("\n=== EVALUATION RESULTS ===")
    for k, v in metrics.items():
        print(f"  {k:40s} {v:.4f}")
    print()

    json_path, md_path = generate_report(args.task, metrics, args.output_dir)
    logger.info("Report saved: %s | %s", json_path, md_path)


if __name__ == "__main__":
    main()
