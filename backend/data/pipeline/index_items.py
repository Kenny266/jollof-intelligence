"""
Embed item description paragraphs and upsert them into the `items` ChromaDB collection.

One document per unique catalogue item (parent_asin as the document ID).
This collection is queried at recommendation time using pre-computed user
preference vectors for grounded, hallucination-free retrieval.

Usage:
    python -m data.pipeline.index_items
    python -m data.pipeline.index_items --batch-size 256 --reset
"""
import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from shared.retrieval.vectorstore import upsert_documents, collection_count, get_collection
from src.config import get_settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

PROCESSED_DIR = Path("data/processed")
ITEMS_FILE = PROCESSED_DIR / "textualized_items.parquet"


def run(batch_size: int = 256, reset: bool = False) -> None:
    if not ITEMS_FILE.exists():
        raise FileNotFoundError(
            f"Missing {ITEMS_FILE}. Run textualize_items.py first."
        )

    logger.info("Loading item paragraphs…")
    df = pd.read_parquet(ITEMS_FILE)
    logger.info("Loaded %d items", len(df))

    settings = get_settings()
    collection_name = settings.chroma_items_collection

    if reset:
        logger.warning("Resetting '%s' ChromaDB collection…", collection_name)
        from shared.retrieval.vectorstore import _get_client
        client = _get_client()
        try:
            client.delete_collection(collection_name)
            logger.info("Deleted collection '%s'", collection_name)
        except Exception:
            pass

    def safe_str(v: object) -> str:
        return str(v) if v is not None and str(v) != "nan" else ""

    def safe_float(v: object) -> float:
        try:
            f = float(v)  # type: ignore[arg-type]
            return f if f == f else 0.0  # filter NaN
        except (TypeError, ValueError):
            return 0.0

    total = len(df)
    for start in tqdm(range(0, total, batch_size), desc="indexing items"):
        batch = df.iloc[start : start + batch_size]

        documents = batch["text_paragraph"].tolist()

        # Use parent_asin as the document ID so each item has exactly one vector
        ids = [safe_str(row.get("parent_asin")) or f"item_{start + i}"
               for i, (_, row) in enumerate(batch.iterrows())]

        metadatas = [
            {
                "parent_asin": safe_str(row.get("parent_asin")),
                "item_title": safe_str(row.get("item_title")),
                "author": safe_str(row.get("author")),
                "categories": safe_str(row.get("categories")),
                "price": safe_str(row.get("price")),
                "average_rating": safe_float(row.get("average_rating")),
            }
            for _, row in batch.iterrows()
        ]

        upsert_documents(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
            collection_name=collection_name,
        )

    total_indexed = collection_count(collection_name)
    logger.info(
        "Item indexing complete. Total documents in '%s': %d",
        collection_name,
        total_indexed,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Embed item description paragraphs into the items ChromaDB collection"
    )
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the items collection before indexing",
    )
    args = parser.parse_args()
    run(batch_size=args.batch_size, reset=args.reset)
