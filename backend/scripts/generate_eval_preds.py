"""
Generate evaluation prediction files from held-out samples.

Without --live, writes baseline preds aligned with refs (for offline metric smoke tests).
With --live, calls Task A/B agents against the running stack (requires DB + Ollama).

Usage:
    python scripts/generate_eval_preds.py
    python scripts/generate_eval_preds.py --live --sample-size 10
    python scripts/generate_eval_preds.py --from-parquet data/processed/merged.parquet
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

EVAL_DIR = Path("data/eval")
MERGED_DEFAULT = Path("data/processed/merged.parquet")


def _write_json(path: Path, data: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    logger.info("Wrote %s (%d rows)", path, len(data))


def build_from_parquet(parquet_path: Path, sample_size: int) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    """Build Task A/B ref sets from merged.parquet."""
    import pandas as pd

    df = pd.read_parquet(parquet_path)
    if df.empty:
        raise ValueError(f"No rows in {parquet_path}")

    sample = df.sample(n=min(sample_size, len(df)), random_state=42)

    task_a_refs: list[dict] = []
    task_a_preds: list[dict] = []
    task_b_refs: list[dict] = []
    task_b_preds: list[dict] = []

    for _, row in sample.iterrows():
        user_id = str(row.get("user_id", ""))
        title = str(row.get("item_title", "Unknown"))
        review = str(row.get("review_text", row.get("text", "")))[:500]
        rating = int(float(row.get("rating", 3)))
        asin = str(row.get("parent_asin", ""))

        task_a_refs.append({
            "user_id": user_id,
            "product_title": title,
            "rating": rating,
            "review": review,
        })
        task_a_preds.append({
            "user_id": user_id,
            "product_title": title,
            "rating": rating,
            "review": review,
        })

        cold_start = False
        task_b_refs.append({
            "user_id": user_id,
            "context": f"Books similar to {title}",
            "cold_start": cold_start,
            "relevant_items": [asin] if asin else [],
        })
        task_b_preds.append({
            "user_id": user_id,
            "context": f"Books similar to {title}",
            "cold_start": cold_start,
            "recommendations": [
                {
                    "item_id": asin,
                    "title": title,
                    "reason": f"Recommended based on interest in {title}.",
                }
            ],
        })

    return task_a_refs, task_a_preds, task_b_refs, task_b_preds


async def build_live_preds(
    task_a_refs: list[dict],
    task_b_refs: list[dict],
) -> tuple[list[dict], list[dict]]:
    """Call agents to produce live predictions."""
    from shared.db.user_history import user_history_repo
    from task_a.agent import UserModelingAgent
    from task_b.agent import RecommendationAgent

    task_a_agent = UserModelingAgent()
    task_b_agent = RecommendationAgent()

    task_a_preds: list[dict] = []
    for ref in task_a_refs:
        history = await user_history_repo.get_history(ref["user_id"])
        product = {
            "item_title": ref["product_title"],
            "author": "",
            "categories": "Books",
            "price": "N/A",
            "description": "",
        }
        result = await task_a_agent.run(ref["user_id"], history, product)
        task_a_preds.append({
            "user_id": ref["user_id"],
            "product_title": ref["product_title"],
            "rating": result["rating"],
            "review": result["review"],
        })

    task_b_preds: list[dict] = []
    for ref in task_b_refs:
        history = await user_history_repo.get_history(ref["user_id"])
        cold_start = len(history) == 0
        result = await task_b_agent.run(
            user_id=ref["user_id"],
            history=history,
            context=ref["context"],
            conversation=[],
            top_k=5,
        )
        task_b_preds.append({
            "user_id": ref["user_id"],
            "context": ref["context"],
            "cold_start": cold_start,
            "recommendations": result.get("recommendations", []),
        })

    return task_a_preds, task_b_preds


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate evaluation JSON files")
    parser.add_argument("--sample-size", type=int, default=20)
    parser.add_argument("--from-parquet", type=str, default="")
    parser.add_argument("--live", action="store_true", help="Call agents for predictions")
    args = parser.parse_args()

    parquet_path = Path(args.from_parquet) if args.from_parquet else MERGED_DEFAULT

    if parquet_path.exists():
        task_a_refs, task_a_preds, task_b_refs, task_b_preds = build_from_parquet(
            parquet_path, args.sample_size
        )
    else:
        logger.warning("Parquet not found at %s — using committed sample refs", parquet_path)
        task_a_refs = json.loads((EVAL_DIR / "task_a_refs.json").read_text(encoding="utf-8"))
        task_b_refs = json.loads((EVAL_DIR / "task_b_refs.json").read_text(encoding="utf-8"))
        task_a_preds = [dict(r) for r in task_a_refs]
        task_b_preds = [dict(r) for r in task_b_refs]

    if args.live:
        logger.info("Generating live predictions via agents…")
        task_a_preds, task_b_preds = asyncio.run(build_live_preds(task_a_refs, task_b_refs))

    _write_json(EVAL_DIR / "task_a_refs.json", task_a_refs)
    _write_json(EVAL_DIR / "task_a_preds.json", task_a_preds)
    _write_json(EVAL_DIR / "task_b_refs.json", task_b_refs)
    _write_json(EVAL_DIR / "task_b_preds.json", task_b_preds)
    logger.info("Evaluation files ready in %s", EVAL_DIR)


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    main()
