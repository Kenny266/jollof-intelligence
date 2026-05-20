# Jollof Intelligence

**DSN x BCT LLM Agent Challenge — Hackathon 3.0**
Data & AI Summit | Deadline: 24 May 2026

Two LLM-powered agents that model human behaviour and deliver personalised book
recommendations — with authentic Nigerian English outputs, powered entirely by
local Qwen3 and DeepSeek-R1 models via Ollama.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Repository Structure](#repository-structure)
3. [Quickstart](#quickstart)
4. [Running with Docker (Recommended)](#running-with-docker-recommended)
5. [Running Locally](#running-locally)
6. [Data Pipeline](#data-pipeline)
7. [API Reference](#api-reference)
8. [Evaluation Suite](#evaluation-suite)
9. [Environment Variables](#environment-variables)
10. [Datasets](#datasets)
11. [Solution Paper](#solution-paper)

---

## Architecture

```
    ┌─────────────────────────────────────────────────────────────┐
    │                    FastAPI (port 8000)                      │
    │  POST /api/v1/task-a/generate-review                        │
    │  POST /api/v1/task-b/recommend                              │
    └──────────────┬──────────────────────────┬───────────────────┘
                   │                          │
        ┌──────────▼──────────┐   ┌───────────▼───────────────┐
        │  Task A Agent       │   │  Task B Agent              │
        │  User Modeling      │   │  Recommendation            │
        │  - Persona Builder  │   │  - Warm/Cold-start routing │
        │  - RAG Retrieval    │   │  - Cross-domain expansion  │
        │  - Rating Predictor │   │  - Multi-turn dialogue     │
        │  - Review Generator │   │  - LLM Reranker            │
        └──────────┬──────────┘   └───────────┬────────────────┘
                   │                          │
        ┌──────────▼──────────────────────────▼───────────────────┐
        │  Shared Services                                        │
        │  - ChromaDB  (persistent, data/chroma_db/)              │
        │  - Nigerian Context System Prompt                        │
        └──────────┬──────────────────────────┬───────────────────┘
                   │                          │
        ┌──────────▼──────────┐   ┌──────────▼──────────┐   ┌──────────▼──────────┐
        │  ollama-qwen        │   │  ollama-judge       │   │  ollama-embed       │
        │  qwen3:1.7b         │   │  deepseek-r1:1.5b   │   │  nomic-embed-text   │
        │  port 8001          │   │  port 8002          │   │  port 8003          │
        │  (agent inference)  │   │  (eval / judge)     │   │  (vector embed)     │
        └─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

Embeddings are served by Ollama over HTTP (`POST /api/embeddings`) — the API
container does not bundle PyTorch or sentence-transformers. This keeps the Docker
image lean and avoids multi-GB CUDA wheel downloads at build time.

---

## Repository Structure

```
backend/
├── src/
│   ├── main.py                         # Unified FastAPI entrypoint
│   ├── config.py                       # Pydantic Settings (env-driven config)
│   ├── models/
│   │   ├── task_a.py                   # ReviewRequest / ReviewResponse
│   │   └── task_b.py                   # RecommendRequest / RecommendResponse
│   ├── router/
│   │   ├── user_modelling_router.py    # POST /api/v1/task-a/generate-review
│   │   └── recommender_router.py       # POST /api/v1/task-b/recommend
│   └── controllers/
│       ├── user_modelling_controller.py
│       └── recommender_controller.py
├── shared/
│   ├── llm/
│   │   ├── client.py                   # Async Ollama HTTP client
│   │   └── nigerian_context.py         # Nigerian persona system prompt
│   ├── persona/
│   │   └── builder.py                  # Persona builder + cold-start fallback
│   └── retrieval/
│       ├── vectorstore.py              # ChromaDB + Ollama embedding client
│       └── rag.py                      # RAG context assembly
├── task_a/
│   ├── agent.py                        # Task A orchestrator
│   ├── rating.py                       # LLM-guided rating predictor
│   └── prompts/v1/review_prompt.txt    # Versioned prompt template
├── task_b/
│   ├── agent.py                        # Task B orchestrator
│   ├── coldstart.py                    # 3-tier cold-start strategy
│   ├── cross_domain.py                 # Cross-subcategory reasoning
│   ├── dialogue.py                     # Multi-turn dialogue manager
│   └── prompts/v1/recommend_prompt.txt
├── data/
│   ├── pipeline/
│   │   ├── download.py                 # HuggingFace dataset downloader
│   │   ├── preprocess.py               # Clean + merge reviews + metadata
│   │   ├── textualize.py               # Structured -> natural language
│   │   └── index.py                    # Embed + store in ChromaDB
│   └── raw/ (gitignored)
│   └── processed/ (gitignored)
├── eval/
│   ├── suite.py                        # CLI evaluation runner
│   ├── task_a_metrics.py               # ROUGE, BERTScore, BLEU, RMSE
│   ├── task_b_metrics.py               # NDCG@10, Hit Rate, MRR
│   ├── deepeval_metrics.py             # DeepEval RAG metrics
│   ├── behavioral_fidelity.py          # LLM-as-judge fidelity scoring
│   └── generate_report.py             # JSON + Markdown report generator
├── notebooks/                          # EDA and exploration
├── paper/                              # Solution paper PDF
├── Dockerfile
├── docker-compose.yml
├── requirements.txt            # Production API dependencies (no torch)
├── requirements-eval.txt       # Eval-only extras (bert-score, deepeval, datasets…)
└── .env.example
```

---

## Quickstart

### Prerequisites

- Docker and Docker Compose installed
- At least 8 GB free disk space (for Ollama model weights across three services)
- 8+ GB RAM recommended

### 1. Clone and configure

```bash
git clone <repo-url>
cd jollof-intelligence/backend
cp .env.example .env
```

### 2. Build and start all services

```bash
# Starts three Ollama services + FastAPI app
make docker-up
# or: docker compose --profile cpu-local up --build -d
```

On first run, each Ollama container pulls its model automatically:

| Service | Model | Approx. size | Cached at |
|---|---|---|---|
| `ollama-qwen` | `qwen3:1.7b` | ~1.1 GB | `./ollama_models/deepseek/` |
| `ollama-judge` | `deepseek-r1:1.5b` | ~1 GB | `./ollama_models/judge/` |
| `ollama-embed` | `nomic-embed-text` | ~274 MB | `./ollama_models/embed/` |

The API container waits until all three Ollama services are healthy before starting.
Subsequent `docker-up` calls reuse cached weights and start in seconds.

### 3. Ingest data (first run only)

```bash
# Inside the running app container:
docker exec -it jollof-api bash

# Download datasets (~50K reviews, ~5 min with good internet)
python -m data.pipeline.download --max-users 10000 --min-reviews 5

# Preprocess and merge
python -m data.pipeline.preprocess

# Textualize
python -m data.pipeline.textualize

# Embed and index into ChromaDB
python -m data.pipeline.index
```

### 4. Verify the API

```bash
curl http://localhost:8000/health
# -> {"status": "ok", "model": "deepseek-r1:1.5b", ...}

curl http://localhost:8000/docs
# -> Interactive Swagger UI
```

---

## Running with Docker (Recommended)

```bash
# Start all services (3 Ollama containers + API)
make docker-up

# Stop all services
make docker-down

# View logs
make docker-logs
docker compose logs -f app
docker compose logs -f ollama-embed

# Open a shell inside the running API container
make docker-shell

# Wipe containers and rebuild from scratch
make docker-reset

# Rebuild only the app (after code changes)
docker compose --profile cpu-local up --build app
```

**Services and ports:**

| Container | Host port | Purpose |
|---|---|---|
| `jollof-api` | 8000 | FastAPI application |
| `ollama-qwen` | 8001 | Agent inference — `qwen3:1.7b` (Task A & B) |
| `ollama-judge` | 8002 | Evaluation / LLM-as-judge — `deepseek-r1:1.5b` |
| `ollama-embed` | 8003 | Text embeddings — `nomic-embed-text` |

---

## Running Locally

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 2. Install dependencies
pip install -r requirements.txt

# For running the evaluation suite (adds bert-score, deepeval, datasets, etc.):
pip install -r requirements-eval.txt

# 3. Start Ollama and pull required models
ollama pull qwen3:1.7b           # agent inference (Task A & B)
ollama pull deepseek-r1:1.5b     # for eval / judge metrics
ollama pull nomic-embed-text     # for ChromaDB embeddings
ollama serve                     # runs on localhost:11434

# 4. Set environment variables
cp .env.example .env
# Edit .env for local Ollama (all three services point to the same instance):
#   OLLAMA_BASE_URL=http://localhost:11434
#   OLLAMA_JUDGE_URL=http://localhost:11434
#   OLLAMA_EMBED_URL=http://localhost:11434
#   AGENT_MODEL=qwen3:1.7b
#   JUDGE_MODEL=deepseek-r1:1.5b
#   EMBEDDING_MODEL=nomic-embed-text

# 5. Run the API
cd backend
uvicorn src.main:app --reload --port 8000

# 6. Open docs
# http://localhost:8000/docs
```

---

## Data Pipeline

Run these steps once before making API calls. Each step saves output files that
the next step reads from.

```bash
# Step 1: Download Amazon Books datasets from HuggingFace (~15% sample)
python -m data.pipeline.download --max-users 10000 --min-reviews 5
# Output: data/raw/reviews.jsonl, data/raw/metadata.jsonl

# Step 2: Merge reviews with item metadata
python -m data.pipeline.preprocess
# Output: data/processed/merged.parquet

# Step 3: Seed the relational database (SQLite at data/jollof.db)
# Populates users, user_reviews, and items tables from merged.parquet
python -m data.pipeline.seed_db
# Output: data/jollof.db

# Step 4: Convert to natural language paragraphs
python -m data.pipeline.textualize
# Output: data/processed/textualized.parquet

# Step 5: Embed and index into ChromaDB
# Requires ollama-embed to be running (Docker) or `ollama serve` (local)
python -m data.pipeline.index --batch-size 512
# Output: data/chroma_db/ (persistent vector store)

# Optional: reset and re-index (required after changing EMBEDDING_MODEL)
python -m data.pipeline.index --reset

# Or run the entire pipeline in one command:
make pipeline
```

> **Note:** Embeddings are generated via Ollama (`nomic-embed-text`, 768-d vectors).
> If you switch embedding models, delete the existing ChromaDB collection with
> `--reset` and re-run the index step — vector dimensions must match.
>
> The relational DB (`data/jollof.db`) is seeded once via `seed_db` and then kept
> up-to-date at runtime: Task A writes generated reviews back to the DB and ChromaDB
> automatically after each request.

---

## API Reference

### Health Check

```
GET /health
```

```json
{"status": "ok", "model": "qwen3:1.7b", "tasks": ["task-a", "task-b"]}
```

---

### Task A — Simulate User Review

```
POST /api/v1/task-a/generate-review
Content-Type: application/json
```

**Request (warm-start — user history fetched from DB automatically):**

```json
{
  "user_id": "AFKZENTNBQ7A7V7UXW5JJI6UGRYQ",
  "product": {
    "item_title": "Things Fall Apart",
    "author": "Chinua Achebe",
    "categories": "Books > Literature & Fiction > African Literature",
    "price": "12.99",
    "description": "A story of pre-colonial Africa and the clash between tradition and colonialism."
  }
}
```

You may also pass `parent_asin` to let the API look up item metadata from the catalogue (request fields override catalogue values):

```json
{
  "user_id": "AFKZENTNBQ7A7V7UXW5JJI6UGRYQ",
  "product": {
    "parent_asin": "0385474547",
    "item_title": "Things Fall Apart"
  }
}
```

**Response:**

```json
{
  "user_id": "AFKZENTNBQ7A7V7UXW5JJI6UGRYQ",
  "rating": 5,
  "review": "See ehn, this Achebe book na masterpiece no be lie. I've read many African literature titles but this one? E don do for everyone. The way Okonkwo's story unfolds — sharp sharp, no time to breathe...",
  "persona_summary": {
    "avg_rating": 4.0,
    "top_categories": ["Books > Literature & Fiction"],
    "tone": "concise",
    "sentiment_tendency": "positive",
    "cold_start": false
  }
}
```

**Cold-start example (user with no history in DB — API detects automatically):**

```json
{
  "user_id": "NEW_USER_001",
  "product": {
    "item_title": "Atomic Habits",
    "author": "James Clear",
    "categories": "Books > Self-Help",
    "price": "14.99"
  }
}
```

---

### Task B — Get Recommendations

```
POST /api/v1/task-b/recommend
Content-Type: application/json
```

**Warm-start request (history fetched from DB automatically):**

```json
{
  "user_id": "AFKZENTNBQ7A7V7UXW5JJI6UGRYQ",
  "context": "Looking for something similar but set in modern Nigeria",
  "conversation": [],
  "top_k": 5
}
```

**Cold-start request (no DB history — describe the user in `context`):**

```json
{
  "user_id": "NEW_USER_002",
  "context": "22-year-old Nigerian student who loves sci-fi and wants something thought-provoking but not too long",
  "conversation": [],
  "top_k": 5
}
```

**Multi-turn refinement request:**

```json
{
  "user_id": "AFKZENTNBQ7A7V7UXW5JJI6UGRYQ",
  "context": "Something lighter this time",
  "conversation": [
    {"role": "user", "content": "Recommend African fiction"},
    {"role": "assistant", "content": "I recommended Things Fall Apart and Purple Hibiscus."}
  ],
  "top_k": 3
}
```

**Response:**

```json
{
  "user_id": "AFKZENTNBQ7A7V7UXW5JJI6UGRYQ",
  "recommendations": [
    {
      "item_id": "B09BGPFTDB",
      "title": "Half of a Yellow Sun",
      "author": "Chimamanda Ngozi Adichie",
      "categories": "Books > Literature & Fiction > African Literature",
      "price": "13.49",
      "score": 0.94,
      "reason": "Abeg, if you liked Things Fall Apart, Half of a Yellow Sun go give you that same depth. The Biafran War setting na real eye-opener, and Adichie's writing style — e sweet ehn."
    }
  ],
  "follow_up": "You prefer historical fiction or something set in present-day Nigeria?",
  "cold_start": false
}
```

---

## Evaluation Suite

### Standard Metrics

```bash
# Task A: ROUGE, BERTScore, BLEU, RMSE
python -m eval.suite \
  --task a \
  --preds data/processed/task_a_predictions.json \
  --refs  data/processed/task_a_references.json

# Task B: NDCG@10, Hit Rate@10, MRR
python -m eval.suite \
  --task b \
  --preds data/processed/task_b_predictions.json \
  --refs  data/processed/task_b_ground_truth.json \
  --k 10
```

### DeepEval RAG Metrics (requires ollama-judge running)

```bash
# Adds: Answer Relevancy, Faithfulness, Contextual Relevancy, G-Eval
# Uses JUDGE_MODEL (deepseek-r1:7b) via OLLAMA_JUDGE_URL
python -m eval.suite --task a --preds ... --refs ... --deepeval
```

### Behavioural Fidelity (Task A only)

```bash
# Adds: LLM-as-judge persona match + Nigerian persona score
# Also uses ollama-judge (JUDGE_MODEL)
python -m eval.suite --task a --preds ... --refs ... --fidelity
```

### Full evaluation (all metrics)

```bash
python -m eval.suite --task a --preds ... --refs ... --deepeval --fidelity
```

Reports are saved to `eval/reports/` in both JSON and Markdown formats.

---

## Environment Variables

Copy `.env.example` to `.env` and edit as needed.

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://ollama-qwen:11434` | Ollama URL for agent inference (Task A & B) |
| `AGENT_MODEL` | `qwen3:1.7b` | Agent LLM — generator (Task A: no-think, Task B: think) |
| `OLLAMA_JUDGE_URL` | `http://ollama-judge:11434` | Ollama URL for evaluation / LLM-as-judge |
| `JUDGE_MODEL` | `deepseek-r1:1.5b` | Judge LLM model name (DeepEval, behavioural fidelity) |
| `OLLAMA_EMBED_URL` | `http://ollama-embed:11434` | Ollama URL for text embeddings |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Ollama embedding model (768-d vectors) |
| `CHROMA_DB_PATH` | `data/chroma_db` | ChromaDB persistence directory |
| `CHROMA_COLLECTION` | `reviews` | ChromaDB collection name |
| `RETRIEVAL_TOP_K` | `10` | Default number of retrieved documents |
| `LLM_TEMPERATURE` | `0.7` | Generation temperature |
| `LLM_TOP_P` | `0.8` | Top-p nucleus sampling |
| `LLM_MAX_TOKENS` | `512` | Default max new tokens |
| `LOG_LEVEL` | `INFO` | Logging level |
| `DATABASE_URL` | `sqlite:///data/jollof.db` | Relational DB for user history. Use `postgresql+asyncpg://...` for Postgres |

---

## Datasets

| Dataset | Source | Usage |
|---|---|---|
| Amazon Reviews 2023 — Books Reviews | [HuggingFace](https://huggingface.co/datasets/cogsci13/Amazon-Reviews-2023-Books-Review) | User review history, ratings, timestamps |
| Amazon Reviews 2023 — Books Metadata | [HuggingFace](https://huggingface.co/datasets/cogsci13/Amazon-Reviews-2023-Books-Meta) | Item titles, authors, categories, prices |

**Citation:**
```bibtex
@article{hou2024bridging,
  title={Bridging Language and Items for Retrieval and Recommendation},
  author={Hou, Yupeng and Li, Jiacheng and He, Zhankui and Yan, An and Chen, Xiusi and McAuley, Julian},
  journal={arXiv preprint arXiv:2403.03952},
  year={2024}
}
```

---

## Solution Paper

The solution paper is located at `paper/solution_paper.pdf`.

It covers:
1. Problem framing and motivation
2. System architecture and design decisions
3. Task A: User Modeling pipeline (persona builder, RAG, Nigerian context)
4. Task B: Recommendation pipeline (cold-start strategy, cross-domain reasoning, multi-turn dialogue)
5. Evaluation methodology and results
6. Ablation studies
7. Limitations and future work

---

## Technology Stack

| Component | Technology | Reason |
|---|---|---|
| Agent LLM | Qwen3:1.7b via Ollama | Fast, naturalistic text; task-specific think/no-think modes |
| Judge LLM | DeepSeek-R1:1.5b via Ollama | Reasoning-always model — better as evaluator than generator |
| Embeddings | nomic-embed-text via Ollama | Served over HTTP — no PyTorch in the API image |
| Vector DB | ChromaDB | Persistent, metadata-filterable, Docker-friendly |
| Relational DB | SQLite (aiosqlite) | User history and review persistence; swap to Postgres via `DATABASE_URL` |
| API Framework | FastAPI | Async, auto-docs, Pydantic validation |
| Evaluation | ROUGE + BERTScore + BLEU + DeepEval | Covers all rubric metrics (eval-only dependencies in `requirements-eval.txt`) |
