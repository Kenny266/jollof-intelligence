"""
Embed textualized records and load them into ChromaDB.

Chunking strategy: each record is one document (a single review paragraph).
This is appropriate because each unit is already a focused, semantically
coherent text (~100-200 tokens) tied to a specific user-item interaction.

Metadata stored per document:
  user_id, parent_asin, rating, main_category, categories, average_rating,
  item_title, author, price, timestamp

Usage:
    python -m data.pipeline.index
    python -m data.pipeline.index --batch-size 512 --reset
"""
import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Allow imports from backend root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.retrieval.vectorstore import upsert_documents, collection_count, get_collection

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROCESSED_DIR = Path("data/processed")
TEXTUALIZED_FILE = PROCESSED_DIR / "textualized.parquet"


def run(batch_size: int = 512, reset: bool = False) -> None:
    if not TEXTUALIZED_FILE.exists():
        raise FileNotFoundError(f"Missing {TEXTUALIZED_FILE}. Run textualize.py first.")

    logger.info("Loading textualized data…")
    df = pd.read_parquet(TEXTUALIZED_FILE)
    logger.info("Loaded %d rows", len(df))

    if reset:
        logger.warning("Resetting ChromaDB collection…")
        from shared.retrieval.vectorstore import _get_client
        client = _get_client()
        from src.config import get_settings
        col_name = get_settings().chroma_collection
        try:
            client.delete_collection(col_name)
        except Exception:
            pass

    total = len(df)
    for start in tqdm(range(0, total, batch_size), desc="indexing batches"):
        batch = df.iloc[start : start + batch_size]

        documents = batch["text_paragraph"].tolist()
        ids = [
            f"{row.user_id}_{row.parent_asin}_{i}"
            for i, (_, row) in enumerate(batch.iterrows())
        ]

        def safe_str(v) -> str:
            return str(v) if v is not None and str(v) != "nan" else ""

        def safe_float(v) -> float:
            try:
                return float(v)
            except (TypeError, ValueError):
                return 0.0

        metadatas = [
            {
                "user_id": safe_str(row.get("user_id")),
                "parent_asin": safe_str(row.get("parent_asin")),
                "rating": safe_float(row.get("rating")),
                "main_category": safe_str(row.get("main_category")),
                "categories": safe_str(row.get("categories")),
                "average_rating": safe_float(row.get("average_rating")),
                "item_title": safe_str(row.get("item_title")),
                "author": safe_str(row.get("author")),
                "price": safe_str(row.get("price")),
                "timestamp": safe_str(row.get("timestamp")),
            }
            for _, row in batch.iterrows()
        ]

        upsert_documents(documents=documents, metadatas=metadatas, ids=ids)

    total_indexed = collection_count()
    logger.info("Indexing complete. Total documents in collection: %d", total_indexed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index textualized records into ChromaDB")
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--reset", action="store_true", help="Delete and recreate the collection before indexing")
    args = parser.parse_args()
    run(batch_size=args.batch_size, reset=args.reset)
