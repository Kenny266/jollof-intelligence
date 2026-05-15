#!/bin/bash
# Download and ingest Amazon Reviews into PostgreSQL
set -e

echo "=== Step 1: Start the database ==="
docker-compose up -d db
echo "Waiting for Postgres to be healthy..."
sleep 8

echo ""
echo "=== Step 2: Run ingestion pipeline ==="
echo "This downloads Electronics, All_Beauty, and Food_and_Drink"
echo "from HuggingFace and loads into PostgreSQL (50k rows each)."
echo ""
docker-compose --profile ingest up ingest

echo ""
echo "=== Step 3: Verify data ==="
docker-compose run --rm ingest python -m database.scripts.verify
