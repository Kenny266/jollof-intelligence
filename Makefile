.PHONY: help setup setup-env install test \
        pipeline-download pipeline-preprocess pipeline-seed pipeline-textualize pipeline-index \
        pipeline-textualize-items pipeline-index-items pipeline-index-user-reviews pipeline \
        run docker-build docker-up docker-down docker-stop docker-start docker-logs docker-shell docker-clean \
        eval-generate eval-a eval-b eval-all docker-clean-data \
        package-models package-demo-data package-submission \
        fetch-models fetch-demo-data judge-setup


# ──────────────────────────────────────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Jollof Intelligence – available targets"
	@echo "────────────────────────────────────────"
	@echo "  setup               Create .venv and install all dependencies"
	@echo "  setup-env           Copy .env.example to .env at repo root (if missing)"
	@echo "  install             Install deps into the active venv (CI / Docker)"
	@echo ""
	@echo "  Top-level shortcuts"
	@echo "  test                Run code quality checks"
	@echo "  pipeline            Download raw data and run the full ingestion pipeline (includes DB seed)"
	@echo "  pipeline-textualize-items   Generate item description paragraphs for the items collection"
	@echo "  pipeline-index-items        Embed item paragraphs into the ChromaDB items collection"
	@echo "  pipeline-index-user-reviews Index review paragraphs into the user_reviews collection"
	@echo "  eval-generate       Build evaluation JSON from parquet or samples"
	@echo "  eval-a              Run Task A evaluation suite"
	@echo "  eval-b              Run Task B evaluation suite"
	@echo "  eval-all            Run both evaluation suites"
	@echo ""
	@echo "  Docker"
	@echo "  docker-up           Start Ollama + backend + frontend via docker compose"
	@echo "  docker-down         Stop and remove containers"
	@echo "  docker-stop         Stop containers"
	@echo "  docker-start        Start containers"
	@echo "  docker-logs         Tail logs from all containers"
	@echo "  docker-shell        Open a bash shell inside the running app container"
	@echo "  docker-clean        Remove caches and build artefacts"
	@echo ""
	@echo "  Submission (maintainer)"
	@echo "  package-models      Bundle Ollama model weights → dist/ollama_models.tar.gz"
	@echo "  package-demo-data   Bundle SQLite + ChromaDB    → dist/demo_data.tar.gz"
	@echo "  package-submission  Both bundles + SHA256 checksums"
	@echo ""
	@echo "  Judge quick setup"
	@echo "  fetch-models        Download + extract models bundle (requires MODELS_BUNDLE_URL in .env)"
	@echo "  fetch-demo-data     Download + extract demo data (requires DEMO_DATA_BUNDLE_URL in .env)"
	@echo "  judge-setup         Full judge setup: env + fetch models + fetch demo data"

# ──────────────────────────────────────────────────────────────────────────────
# Setup
# ──────────────────────────────────────────────────────────────────────────────

setup-env:
	cp -n .env.example .env || true

# ──────────────────────────────────────────────────────────────────────────────
# Top-level shortcuts
# ──────────────────────────────────────────────────────────────────────────────

# Run code quality checks
test:
	ruff check .
	ruff format .
	docker exec -it -w /app backend-api python -m mypy .
	docker exec -it -w /app backend-api python -m yamllint .
	docker exec -it -w /app backend-api python -m pytest --ignore=tests/eval
	MSYS_NO_PATHCONV=1 docker exec -it -w /app backend-api python -m pytest tests/eval/ -m offline -k "json_schema or accuracy or adherence or math" --tb=short -q --no-header
	docker exec -it -w /app backend-api python -m common.prompts_check
	docker exec -it -w /app backend-api python scripts/fetch_recent_market_context.py


# ──────────────────────────────────────────────────────────────────────────────
# Data pipeline
# ──────────────────────────────────────────────────────────────────────────────
pipeline-download:
	@echo "Running download pipeline..."
	docker exec -it -w /app backend-api python -m data.pipeline.download
	@echo "✓ Download pipeline complete"

pipeline-preprocess:
	@echo "Running preprocess pipeline..."
	docker exec -it -w /app backend-api python -m data.pipeline.preprocess
	@echo "✓ Preprocess pipeline complete"

pipeline-seed:
	@echo "Running seed pipeline..."
	docker exec -it -w /app backend-api python -m data.pipeline.seed_db
	@echo "✓ Seed pipeline complete"

pipeline-textualize:
	@echo "Running textualize pipeline..."
	docker exec -it -w /app backend-api python -m data.pipeline.textualize
	@echo "✓ Textualize pipeline complete"

pipeline-index:
	@echo "Running index pipeline (reviews collection for Task A RAG)..."
	docker exec -it -w /app backend-api python -m data.pipeline.index
	@echo "✓ Index pipeline complete"

pipeline-textualize-items:
	@echo "Running item textualization pipeline..."
	docker exec -it -w /app backend-api python -m data.pipeline.textualize_items
	@echo "✓ Item textualization complete"

pipeline-index-items:
	@echo "Indexing item descriptions into the items ChromaDB collection..."
	docker exec -it -w /app backend-api python -m data.pipeline.index_items
	@echo "✓ Item indexing complete"

pipeline-index-user-reviews:
	@echo "Indexing review paragraphs into the user_reviews ChromaDB collection..."
	docker exec -it -w /app backend-api python -m data.pipeline.index --collection user_reviews
	@echo "✓ User-reviews indexing complete"

pipeline:
	@echo "Running full pipeline..."
	make pipeline-download
	make pipeline-preprocess
	make pipeline-seed
	make pipeline-textualize
	make pipeline-index
	make pipeline-textualize-items
	make pipeline-index-items
	make pipeline-index-user-reviews
	@echo "✓ Full pipeline complete"
	@echo ""
	@echo ""
	@echo "✓ API: http://localhost:8000/docs | UI: http://localhost:5173"


# ──────────────────────────────────────────────────────────────────────────────
# Docker
# ──────────────────────────────────────────────────────────────────────────────

docker-up:
	docker compose --profile cpu-local up --build -d
	@echo "✓ API: http://localhost:8000/docs | UI: http://localhost:5173"

docker-down:
	docker compose --profile cpu-local down

docker-stop:
	docker compose --profile cpu-local stop ollama-generation ollama-judge ollama-embed backend frontend

docker-start:
	docker compose --profile cpu-local start ollama-generation ollama-judge ollama-embed backend frontend

docker-logs:
	docker compose --profile cpu-local logs -f

docker-shell:
	docker exec -it backend-api bash

docker-clean:
# Wipe, stop and remove all containers (incl. Ollama) and files
	docker compose --profile cpu-local down -v
	cd backend && rm -rf proto/generated .pytest_cache .mypy_cache .ruff_cache
	-docker rm -f ollama-generation ollama-judge ollama-embed frontend-web backend-api 2>/dev/null || true
	@echo "✓ Clean"

docker-clean-data:
	@echo "Cleaning data..."
	rm -f backend/data/jollof.db
	rm -f backend/data/raw/*
	rm -f backend/data/processed/*
	rm -rf backend/data/chroma_db/
	@echo "✓ Data cleaned"


docker-reset:
	make docker-clean
	make docker-clean-data
	sleep 5
	make docker-up


# ──────────────────────────────────────────────────────────────────────────────
# Submission packaging (maintainer)
# Run after: make docker-up && make pipeline
# ──────────────────────────────────────────────────────────────────────────────

package-models:
	@echo "Packaging Ollama model weights..."
	bash scripts/package_submission_assets.sh pack-models
	@echo "✓ dist/ollama_models.tar.gz ready"

package-demo-data:
	@echo "Packaging demo data (SQLite + ChromaDB)..."
	bash scripts/package_submission_assets.sh pack-demo-data
	@echo "✓ dist/demo_data.tar.gz ready"

package-submission:
	@echo "Creating submission bundles..."
	bash scripts/package_submission_assets.sh pack-all
	@echo ""
	@echo "Upload dist/*.tar.gz to GitHub Release, then set in .env:"
	@echo "  MODELS_BUNDLE_URL=<url>"
	@echo "  DEMO_DATA_BUNDLE_URL=<url>"

# ──────────────────────────────────────────────────────────────────────────────
# Judge quick setup
# Run: make judge-setup && make docker-up
# ──────────────────────────────────────────────────────────────────────────────

fetch-models:
	@echo "Fetching Ollama model bundle..."
	bash scripts/package_submission_assets.sh fetch-models

fetch-demo-data:
	@echo "Fetching demo data bundle..."
	bash scripts/package_submission_assets.sh fetch-demo-data

judge-setup: setup-env fetch-models fetch-demo-data
	@echo ""
	@echo "✓ Judge setup complete. Run: make docker-up"
	@echo "  API docs → http://localhost:8000/docs"
	@echo "  Demo UI  → http://localhost:5173"


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation
# ──────────────────────────────────────────────────────────────────────────────
eval-generate:
	@echo "Generating evaluation datasets..."
	cd backend && python scripts/generate_eval_preds.py
	@echo "✓ Evaluation datasets written to backend/data/eval/"

eval-a:
	@echo "Running evaluation suite (Task A)..."
	cd backend && python -m eval.suite --task a \
	  --preds data/eval/task_a_preds.json \
	  --refs data/eval/task_a_refs.json --fidelity

eval-b:
	@echo "Running evaluation suite (Task B)..."
	cd backend && python -m eval.suite --task b \
	  --preds data/eval/task_b_preds.json \
	  --refs data/eval/task_b_refs.json --k 10

eval-all:
	@echo "Downloading dependencies"
	cd backend && pip install -r requirements-eval.txt
	@echo "✓ Dependencies downloaded"
	@echo ".............."
	@echo ".............."
	@echo ".............."
	@echo "Generating evaluation datasets..."
	cd backend && python scripts/generate_eval_preds.py
	@echo "✓ Evaluation datasets written to backend/data/eval/"
	@echo "Running evaluation suite..."
	@echo "Running evaluation suite (Task A)..."
	make eval-a
	@echo "Running evaluation suite (Task B)..."
	make eval-b
	@echo "✓ Evaluation complete – reports in eval/reports/"
