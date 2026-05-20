"""
Download and save the Amazon Reviews 2023 Books dataset from HuggingFace.

Samples a workable subset (users with >= MIN_REVIEWS interactions) to keep
vector indexing tractable in a single-container deployment.

Uses a single HTTP stream (15% of dataset via split slice) written to a temp
file, then two fast local-disk passes to count and filter — avoids the httpx
client-closed error caused by re-opening an exhausted streaming connection.

Usage:
    python -m data.pipeline.download
    python -m data.pipeline.download --max-users 5000 --min-reviews 5
"""
import argparse
import json
import logging
from pathlib import Path

from datasets import load_dataset
from tqdm import tqdm

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

RAW_DIR = Path("data/raw")
REVIEWS_FILE = RAW_DIR / "reviews.jsonl"
META_FILE = RAW_DIR / "metadata.jsonl"
TMP_REVIEWS_FILE = RAW_DIR / "reviews.tmp.jsonl"

REVIEWS_DATASET = "cogsci13/Amazon-Reviews-2023-Books-Review"
META_DATASET = "cogsci13/Amazon-Reviews-2023-Books-Meta"

rows_limit = 50000
max_users = 10000
min_reviews = 5

def download_reviews(max_users: int = max_users, min_reviews: int = min_reviews) -> set[str]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # --- HTTP pass (single connection, 15% slice) → temp file ---
    logger.info(f"Streaming {rows_limit} rows of reviews from HuggingFace to temp file…")
    ds = load_dataset(
        REVIEWS_DATASET,
        "default",
        split="full",
        trust_remote_code=True,
        streaming=True,
    )
    if rows_limit is not None:
        ds = ds.take(rows_limit)

    tmp_count = 0

    with TMP_REVIEWS_FILE.open("w", encoding="utf-8") as f:
        for row in tqdm(ds, desc="streaming to temp"):
            uid = row.get("user_id", "")
            if not uid:
                continue
            record = {
                "user_id": uid,
                "parent_asin": row.get("parent_asin") or row.get("asin"),
                "rating": row.get("rating"),
                "title": row.get("title", ""),
                "text": row.get("text", ""),
                "timestamp": row.get("timestamp"),
                "helpful_vote": row.get("helpful_vote", 0),
                "verified_purchase": row.get("verified_purchase", False),
            }
            f.write(json.dumps(record) + "\n")
            tmp_count += 1
    logger.info("Temp file written: %d rows", tmp_count)

    # --- Disk pass 1: count reviews per user ---
    logger.info("Counting reviews per user from temp file…")
    user_counts: dict[str, int] = {}
    with TMP_REVIEWS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            uid = json.loads(line)["user_id"]
            user_counts[uid] = user_counts.get(uid, 0) + 1

    eligible = {u for u, c in user_counts.items() if c >= min_reviews}
    logger.info("%d eligible users (>= %d reviews)", len(eligible), min_reviews)
    sampled_users = set(list(eligible)[:max_users])
    logger.info("Sampled %d users", len(sampled_users))

    # --- Disk pass 2: filter sampled users → final file ---
    logger.info("Writing filtered reviews to %s…", REVIEWS_FILE)
    written = 0

    logger.info("Streaming from temp file to final file…")
    with TMP_REVIEWS_FILE.open("r", encoding="utf-8") as src, REVIEWS_FILE.open("w", encoding="utf-8") as dst:
        for line in src:
            if json.loads(line)["user_id"] in sampled_users:
                dst.write(line)
                written += 1

    TMP_REVIEWS_FILE.unlink()
    logger.info("Wrote %d reviews to %s", written, REVIEWS_FILE)

    # Collect all parent_asins present in the final filtered reviews file
    reviewed_asins: set[str] = set()
    with REVIEWS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            asin = json.loads(line).get("parent_asin")
            if asin:
                reviewed_asins.add(asin)
    logger.info("Collected %d unique parent_asin values from reviews", len(reviewed_asins))
    return reviewed_asins


def download_metadata(required_asins: set[str] | None = None) -> None:
    """Stream metadata, keeping only records whose parent_asin appears in reviews."""
    label = f"{rows_limit} rows" if required_asins is None else f"{len(required_asins)} target ASINs"
    logger.info(f"Loading item metadata from HuggingFace ({label})…")
    ds = load_dataset(META_DATASET, "default", split="full", trust_remote_code=True, streaming=True)

    if rows_limit is not None:
        ds = ds.take(rows_limit)

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    written = 0

    # When we know which ASINs we need, scan until all are found (or exhausted).
    # Without a filter set, fall back to the plain row-limit behaviour.
    remaining = set(required_asins) if required_asins else None

    with META_FILE.open("w", encoding="utf-8") as f:
        for row in tqdm(ds, desc="writing metadata"):
            if remaining is not None and row.get("parent_asin") not in remaining:
                continue
            if remaining is None and written >= rows_limit:
                break
            author_raw = row.get("author", "")
            author_name = ""
            if isinstance(author_raw, dict):
                author_name = author_raw.get("name", "")
            elif isinstance(author_raw, str) and author_raw.startswith("{"):
                try:
                    import ast
                    parsed = ast.literal_eval(author_raw)
                    author_name = parsed.get("name", "")
                except Exception:
                    author_name = author_raw

            record = {
                "parent_asin": row.get("parent_asin"),
                "title": row.get("title", ""),
                "main_category": row.get("main_category", "Books"),
                "categories": row.get("categories", []),
                "average_rating": row.get("average_rating"),
                "rating_number": row.get("rating_number"),
                "price": row.get("price"),
                "store": row.get("store", ""),
                "description": row.get("description", []),
                "features": row.get("features", []),
                "author": author_name,
                "details": row.get("details", ""),
            }
            f.write(json.dumps(record) + "\n")
            written += 1
            if remaining is not None:
                remaining.discard(row.get("parent_asin"))
                if not remaining:
                    logger.info("All target ASINs found — stopping metadata stream early.")
                    break

    logger.info("Wrote %d metadata records to %s", written, META_FILE)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Amazon Books datasets")
    parser.add_argument("--max-users", type=int, default=10_000)
    parser.add_argument("--min-reviews", type=int, default=5)
    args = parser.parse_args()
    reviewed_asins = download_reviews(max_users=args.max_users, min_reviews=args.min_reviews)
    download_metadata(required_asins=reviewed_asins)
