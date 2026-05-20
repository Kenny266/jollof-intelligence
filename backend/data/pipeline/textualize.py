"""
Convert structured merged records into natural language paragraphs
optimized for LLM comprehension and embedding quality.

Usage:
    python -m data.pipeline.textualize
"""
import logging
from pathlib import Path

import pandas as pd
from tqdm import tqdm

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROCESSED_DIR = Path("data/processed")
MERGED_FILE = PROCESSED_DIR / "merged.parquet"
TEXTUALIZED_FILE = PROCESSED_DIR / "textualized.parquet"


def _textualize_row(row: pd.Series) -> str:
    """
    Convert a single merged review+metadata row into a natural language paragraph.

    Example output:
        [User AFKZ...] rated 'Chaucer' by Peter Ackroyd 4/5 stars.
        Categories: Books > Literature & Fiction > History & Criticism.
        Review title: 'Not a watercolor book!'. Review: 'It is definitely not...'
        Price: $8.23. Publisher: Chatto & Windus.
    """
    user_id = row.get("user_id", "unknown")
    rating = row.get("rating", "?")
    item_title = row.get("item_title", "Unknown Item")
    author = row.get("author", "")
    categories = row.get("categories", "Books")
    review_title = str(row.get("title", "")).strip()
    review_text = str(row.get("text", "")).strip()
    price = row.get("price", "N/A")
    publisher = row.get("publisher", "")
    avg_rating = row.get("average_rating", "")
    rating_count = row.get("rating_number", "")

    author_part = f" by {author}" if author else ""
    publisher_part = f" Publisher: {publisher}." if publisher else ""
    avg_part = f" Overall product rating: {avg_rating}/5 ({rating_count} ratings)." if avg_rating else ""

    paragraph = (
        f"[User {user_id}] rated '{item_title}'{author_part} {rating}/5 stars. "
        f"Categories: {categories}. "
        f"Review title: '{review_title}'. "
        f"Review: '{review_text[:500]}' "
        f"Price: ${price}.{publisher_part}{avg_part}"
    )
    return paragraph.strip()


def run() -> None:
    if not MERGED_FILE.exists():
        raise FileNotFoundError(f"Missing {MERGED_FILE}. Run preprocess.py first.")

    logger.info("Loading merged data…")
    df = pd.read_parquet(MERGED_FILE)
    logger.info("Loaded %d rows", len(df))

    tqdm.pandas(desc="textualize")
    df["text_paragraph"] = df.progress_apply(_textualize_row, axis=1)

    df.to_parquet(TEXTUALIZED_FILE, index=False)
    logger.info("Saved textualized data to %s", TEXTUALIZED_FILE)


if __name__ == "__main__":
    run()
