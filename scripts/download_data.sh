#!/bin/bash
# Download datasets for DSN-BCT hackathon
set -e

mkdir -p data/raw

echo "==> Downloading Amazon Reviews (Electronics subset via HuggingFace datasets)"
python - << 'PYEOF'
from datasets import load_dataset
ds = load_dataset("McAuley-Lab/Amazon-Reviews-2023", "raw_review_Electronics", split="full", trust_remote_code=True)
ds.to_json("data/raw/amazon_electronics.jsonl")
print(f"Amazon: {len(ds)} records saved")
PYEOF

echo ""
echo "==> Yelp dataset must be downloaded manually (requires agreement):"
echo "    Visit: https://www.yelp.com/dataset"
echo "    Place yelp_academic_dataset_review.json in data/raw/"
echo ""
echo "==> Goodreads dataset:"
echo "    Visit: https://mengtingwan.github.io/data/goodreads.html"
echo "    Download goodreads_reviews_dedup.json.gz into data/raw/"
