"""
Generate item-only description paragraphs for embedding into the `items` ChromaDB collection.

Each row in the output represents one unique catalogue item (parent_asin).
The paragraph is crafted to maximise semantic richness for cosine-similarity
retrieval against user preference vectors.

Usage:
    python -m data.pipeline.textualize_items
"""
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROCESSED_DIR = Path("data/processed")
MERGED_FILE = PROCESSED_DIR / "merged.parquet"
ITEMS_FILE = PROCESSED_DIR / "textualized_items.parquet"


def _textualize_item(row: pd.Series) -> str:
    """
    Build a natural language paragraph that captures the full semantic identity
    of one catalogue item.

    Example output:
        'Atomic Habits' by James Clear. Categories: Books > Self-Help > Personal
        Transformation. Description: No matter your goals, Atomic Habits offers a
        proven framework for improving every day... Average rating: 4.8/5.
        Price: $14.99.
    """
    item_title = str(row.get("item_title") or "Unknown Title").strip()
    author = str(row.get("author") or "").strip()
    categories = str(row.get("categories") or "Books").strip()
    description = str(row.get("description") or "").strip()
    average_rating = row.get("average_rating")
    price = row.get("price")

    author_part = f" by {author}" if author else ""
    desc_part = f" Description: {description[:500]}." if description else ""
    rating_part = f" Average rating: {average_rating}/5." if average_rating else ""
    price_part = f" Price: ${price}." if price else ""

    return (
        f"'{item_title}'{author_part}."
        f" Categories: {categories}."
        f"{desc_part}"
        f"{rating_part}"
        f"{price_part}"
    ).strip()


def run() -> None:
    if not MERGED_FILE.exists():
        raise FileNotFoundError(f"Missing {MERGED_FILE}. Run preprocess.py first.")

    logger.info("Loading merged data…")
    df = pd.read_parquet(MERGED_FILE)
    logger.info("Loaded %d rows", len(df))

    # Deduplicate: one row per catalogue item
    item_cols = ["parent_asin", "item_title", "author", "categories",
                 "description", "average_rating", "price"]
    available = [c for c in item_cols if c in df.columns]
    items_df = df[available].drop_duplicates(subset=["parent_asin"]).copy()
    logger.info("Unique items: %d", len(items_df))

    tqdm.pandas(desc="textualize_items")
    items_df["text_paragraph"] = items_df.progress_apply(_textualize_item, axis=1)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    items_df.to_parquet(ITEMS_FILE, index=False)
    logger.info("Saved item paragraphs to %s (%d items)", ITEMS_FILE, len(items_df))


if __name__ == "__main__":
    run()
