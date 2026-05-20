.PHONY: help setup install test \
        pipeline-download pipeline-preprocess pipeline-seed pipeline-textualize pipeline-index pipeline \
        run docker-build docker-up docker-down docker-stop docker-start docker-logs docker-shell docker-clean \
        eval-a eval-b eval-all


# ──────────────────────────────────────────────────────────────────────────────
# Help
# ──────────────────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "Jollof Intelligence – available targets"
	@echo "────────────────────────────────────────"
	@echo "  setup               Create .venv and install all dependencies"
	@echo "  install             Install deps into the active venv (CI / Docker)"
	@echo ""
	@echo "  Top-level shortcuts"
	@echo "  test                Run code quality checks"
	@echo "  pipeline            Download raw data and run the full ingestion pipeline (includes DB seed)"
	@echo "  eval-a              Run Task A evaluation suite"
	@echo "  eval-b              Run Task B evaluation suite"
	@echo "  eval-all            Run both evaluation suites"
	@echo ""
	@echo "  Docker"
	@echo "  docker-up           Start Ollama + app via docker compose"
	@echo "  docker-down         Stop and remove containers"
	@echo "  docker-stop         Stop containers"
	@echo "  docker-start        Start containers"
	@echo "  docker-logs         Tail logs from all containers"
	@echo "  docker-shell        Open a bash shell inside the running app container"
	@echo "  docker-clean        Remove caches and build artefacts"

# ──────────────────────────────────────────────────────────────────────────────
# Top-level shortcuts
# ──────────────────────────────────────────────────────────────────────────────

# Run code quality checks
test:
	ruff check .
	ruff format .
	docker exec -it -w /app jollof-api python -m mypy .
	docker exec -it -w /app jollof-api python -m yamllint .
	docker exec -it -w /app jollof-api python -m pytest --ignore=tests/eval
	MSYS_NO_PATHCONV=1 docker exec -it -w /app jollof-api python -m pytest tests/eval/ -m offline -k "json_schema or accuracy or adherence or math" --tb=short -q --no-header
	docker exec -it -w /app jollof-api python -m common.prompts_check
	docker exec -it -w /app jollof-api python scripts/fetch_recent_market_context.py


# ──────────────────────────────────────────────────────────────────────────────
# Data pipeline
# ──────────────────────────────────────────────────────────────────────────────
pipeline-download:
	# PYTHONPATH="$(CURDIR)" python -m data.pipeline.download
	docker exec -it -w /app jollof-api python -m data.pipeline.download

pipeline-preprocess:
	docker exec -it -w /app jollof-api python -m data.pipeline.preprocess

pipeline-seed:
	docker exec -it -w /app jollof-api python -m data.pipeline.seed_db

pipeline-textualize:
	docker exec -it -w /app jollof-api python -m data.pipeline.textualize

pipeline-index:
	docker exec -it -w /app jollof-api python -m data.pipeline.index

pipeline:
	@echo "Running full pipeline..."
	make pipeline-download
	make pipeline-preprocess
	make pipeline-seed
	make pipeline-textualize
	make pipeline-index
	@echo "✓ Full pipeline complete"


# ──────────────────────────────────────────────────────────────────────────────
# Docker
# ──────────────────────────────────────────────────────────────────────────────

docker-up:
	docker compose --profile cpu-local up --build -d
	@echo "✓ Services started – API at http://localhost:8000/docs"

docker-down:
	docker compose --profile cpu-local down

docker-stop:
	docker compose --profile cpu-local stop

docker-start:
	docker compose --profile cpu-local start

docker-logs:
	docker compose --profile cpu-local logs -f

docker-shell:
	docker exec -it jollof-api bash

docker-clean:
# Wipe, stop and remove all containers (incl. Ollama) and files
	docker compose --profile cpu-local down -v
	rm -rf proto/generated
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	-docker rm -f ollama-qwen ollama-judge 2>/dev/null || true
	@echo "✓ Clean"

docker-reset:
	make docker-clean
	sleep 5
	make docker-up


# ──────────────────────────────────────────────────────────────────────────────
# Evaluation
# ──────────────────────────────────────────────────────────────────────────────
eval-a:
	@echo "Running evaluation suite (Task A)..."
	PYTHONPATH=$(CURDIR) python -m eval.suite --task a

eval-b:
	@echo "Running evaluation suite (Task B)..."
	PYTHONPATH=$(CURDIR) python -m eval.suite --task b

eval-all:
	@echo "Running evaluation suite..."
	eval-a
	eval-b
	@echo "✓ Evaluation complete – reports in eval/reports/"
