"""
Preprocess and merge reviews with item metadata.

Steps:
1. Load raw JSONL files.
2. Inner-join reviews with metadata on parent_asin.
3. Parse nested author dict and details JSON string.
4. Flatten categories list to comma-separated string.
5. Save merged Parquet file to data/processed/.

Usage:
    python -m data.pipeline.preprocess
"""
import ast
import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
REVIEWS_FILE = RAW_DIR / "reviews.jsonl"
META_FILE = RAW_DIR / "metadata.jsonl"
OUTPUT_FILE = PROCESSED_DIR / "merged.parquet"


def _parse_details(raw: str | dict) -> dict:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        try:
            return ast.literal_eval(raw)
        except Exception:
            return {}


def _flatten_categories(cats: list | str) -> str:
    if isinstance(cats, list):
        return " > ".join(str(c) for c in cats if c)
    return str(cats or "")


def run() -> None:
    if not REVIEWS_FILE.exists():
        raise FileNotFoundError(f"Missing {REVIEWS_FILE}. Run download.py first.")
    if not META_FILE.exists():
        raise FileNotFoundError(f"Missing {META_FILE}. Run download.py first.")

    logger.info("Loading reviews…")
    reviews = pd.read_json(REVIEWS_FILE, lines=True)
    logger.info("Loaded %d reviews", len(reviews))

    logger.info("Loading metadata…")
    meta = pd.read_json(META_FILE, lines=True)
    logger.info("Loaded %d metadata records", len(meta))

    # Parse details
    meta["details_parsed"] = meta["details"].apply(_parse_details)
    meta["publisher"] = meta["details_parsed"].apply(lambda d: d.get("Publisher", "") if isinstance(d, dict) else "")

    # Flatten categories
    meta["categories_str"] = meta["categories"].apply(_flatten_categories)

    # Flatten description list
    meta["description_str"] = meta["description"].apply(
        lambda d: " ".join(d) if isinstance(d, list) else str(d or "")
    )

    # Select and rename metadata columns
    meta_clean = meta[[
        "parent_asin", "title", "main_category", "categories_str",
        "average_rating", "rating_number", "price", "store",
        "description_str", "author", "publisher",
    ]].rename(columns={
        "title": "item_title",
        "categories_str": "categories",
        "description_str": "description",
        "store": "item_store",
    })
    meta_clean = meta_clean.drop_duplicates(subset=["parent_asin"])

    logger.info("Merging on parent_asin…")
    merged = reviews.merge(meta_clean, on="parent_asin", how="inner")
    logger.info("Merged dataset: %d rows", len(merged))

    # Drop rows with empty review text
    merged = merged[merged["text"].str.strip().astype(bool)]
    logger.info("After dropping empty reviews: %d rows", len(merged))

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    merged.to_parquet(OUTPUT_FILE, index=False)
    logger.info("Saved to %s", OUTPUT_FILE)


if __name__ == "__main__":
    run()
