# Jollof Intelligence

**DSN x BCT LLM Agent Challenge — Hackathon 3.0**
Data & AI Summit | Deadline: 24 May 2026

LLM-powered user modeling (Task A) and personalised book recommendations (Task B) with authentic Nigerian English outputs — backed by SQLite for audit and verification, ChromaDB for vector retrieval, and local Qwen3 / DeepSeek-R1 models via Ollama.

## Table of Contents

1. [Architecture](#architecture)
2. [Repository layout](#repository-layout)
3. [Quick start](#quick-start)
4. [Running with Docker (recommended)](#running-with-docker-recommended)
5. [Running locally](#running-locally)
6. [Frontend demo UI](#frontend-demo-ui)
7. [Data pipeline](#data-pipeline)
8. [API reference](#api-reference)
9. [Verification API](#verification-api)
10. [Evaluation suite](#evaluation-suite)
11. [Environment variables](#environment-variables)
12. [Datasets](#datasets)
13. [Technology stack](#technology-stack)
14. [Solution paper](#solution-paper)
15. [Judge quick start](#judge-quick-start)
16. [Sample workflow for judges](#sample-workflow-for-judges)
17. [Submission checklist](#submission-checklist-maintainers)

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
        │  - Persona Builder  │   │  - Warm/cold-start routing │
        │  - RAG Retrieval    │   │  - Vector-similarity search│
        │  - Rating Predictor │   │  - Multi-turn dialogue     │
        │  - Review Generator │   │  - Grounded LLM reranker   │
        └──────────┬──────────┘   └───────────┬────────────────┘
                   │                          │
        ┌──────────▼──────────────────────────▼───────────────────┐
        │  Shared Services                                        │
        │  - ChromaDB (reviews, items, user_reviews collections)  │
        │  - SQLite user history + product catalogue              │
        │  - Nigerian Context System Prompt                       │
        └──────────┬──────────────────────────┬───────────────────┘
                   │                          │
        ┌──────────▼──────────┐   ┌──────────▼──────────┐   ┌──────────▼──────────┐
        │  ollama-generation  │   │  ollama-judge       │   │  ollama-embed       │
        │  qwen3:1.7b         │   │  deepseek-r1:1.5b   │   │  nomic-embed-text   │
        │  port 8001          │   │  port 8002          │   │  port 8003          │
        │  (agent inference)  │   │  (eval / judge)     │   │  (vector embed)     │
        └─────────────────────┘   └─────────────────────┘   └─────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │              React demo UI (port 5173)                      │
    │  Review page (Task A)  ·  Recommend page (Task B)           │
    └─────────────────────────────────────────────────────────────┘
```

**Task B retrieval:** warm users get a preference vector by mean-pooling their review embeddings from the `user_reviews` ChromaDB collection, then query the `items` collection via cosine similarity. Cold-start users embed their free-text `context` on-the-fly and query `items` directly. The LLM reranker reorders candidates and writes explanations, but all returned metadata is grounded to the candidate set — no hallucinated ASINs or titles.

Embeddings are served by Ollama over HTTP (`POST /api/embeddings`). The API container does not bundle PyTorch or sentence-transformers, keeping the Docker image lean.

---

## Repository layout


| Path                                       | Purpose                                               |
| ------------------------------------------ | ----------------------------------------------------- |
| `[backend/](backend/)`                     | FastAPI API, agents, data pipeline, evaluation suite  |
| `[frontend/](frontend/)`                   | React + TypeScript demo UI (Review + Recommend pages) |
| `[docker-compose.yml](docker-compose.yml)` | Ollama services, backend, and frontend containers     |
| `[Makefile](Makefile)`                     | Docker, pipeline, and eval shortcuts                  |
| `[.env.example](.env.example)`             | Environment template (backend + frontend)             |


### Backend

```
backend/
├── src/
│   ├── main.py                         # Unified FastAPI entrypoint
│   ├── config.py                       # Pydantic Settings (env-driven config)
│   ├── models/                         # Request / response schemas
│   ├── router/                         # Task A, Task B, verification routes
│   └── controllers/                    # Business logic layer
├── shared/
│   ├── llm/                            # Async Ollama client + Nigerian context
│   ├── persona/                        # Persona builder + cold-start fallback
│   └── retrieval/                      # ChromaDB + RAG + vector search helpers
├── task_a/                             # User modeling agent
├── task_b/                             # Recommendation agent
├── data/
│   ├── pipeline/                       # Download, preprocess, textualize, index
│   └── raw/ · processed/ (gitignored)
├── eval/                               # Offline evaluation suite + reports
├── notebooks/                          # EDA and exploration
├── paper/                              # Solution paper PDF
├── Dockerfile
├── requirements.txt                    # Production API dependencies
└── requirements-eval.txt               # Eval-only extras
```

### Frontend

```
frontend/
├── src/
│   ├── pages/
│   │   ├── ReviewPage/                 # Task A form + generated review display
│   │   └── RecommendPage/              # Task B form + recommendation cards
│   ├── components/                     # Header, NavTabs, ColdStartBadge, etc.
│   ├── api/apiClient.ts                # Typed fetch wrapper for backend API
│   └── types/                          # API and form types
├── Dockerfile                          # nginx production build
├── vite.config.ts
└── package.json
```

---

## Quick start

### Prerequisites

- Docker and Docker Compose
- At least 8 GB free disk space (Ollama model weights across three services)
- 8+ GB RAM recommended

```bash
# 0. Configure environment (first time only)
cp .env.example .env
# Bundle URLs are pre-filled in .env.example — see Judge quick start if you need to change them

# 1. Download pre-packaged Ollama weights + seeded demo data (one-time, ~3–4 GB)
make judge-setup
# Without make:
cp -n .env.example .env
bash scripts/package_submission_assets.sh fetch-models
bash scripts/package_submission_assets.sh fetch-demo-data

# 2. Start stack (3× Ollama + API + frontend UI)
make docker-up
# Expected output when complete:
# ✓ API: http://localhost:8000/docs | UI: http://localhost:5173
# Without make:
#   API docs → http://localhost:8000/docs
#   Demo UI   → http://localhost:5173
# Then open:
#   API docs → http://localhost:8000/docs
#   Demo UI   → http://localhost:5173

# 3. Stop containers when done (data is preserved)
make docker-stop
# Without make:
docker compose --profile cpu-local stop ollama-generation ollama-judge ollama-embed backend frontend

# 4. Full wipe (removes containers and volumes — use to reset completely)
make docker-clean
# Without make:
docker compose --profile cpu-local down -v
```

> **For judges:** the GitHub Release attached to this submission includes pre-packaged Ollama model weights and seeded demo data (SQLite + all three ChromaDB collections). Demo data lands at `backend/data/jollof.db` and `backend/data/chroma_db/` — no external DB setup. No `make pipeline` needed. See [Judge quick start](#judge-quick-start) for details and fallback instructions.

`make docker-up` prints the service URLs when the stack is up. The API container waits for all three Ollama services to be healthy first (~1–2 min on first run).

**Model weights** are extracted by `make judge-setup` into `backend/ollama_models/{generation,judge,embed}/` — `docker-up` picks them up immediately with no HuggingFace or model pull:


| Service             | Model              | Approx. size | Cached at                           |
| ------------------- | ------------------ | ------------ | ----------------------------------- |
| `ollama-generation` | `qwen3:1.7b`       | ~1.1 GB      | `backend/ollama_models/generation/` |
| `ollama-judge`      | `deepseek-r1:1.5b` | ~1 GB        | `backend/ollama_models/judge/`      |
| `ollama-embed`      | `nomic-embed-text` | ~274 MB      | `backend/ollama_models/embed/`      |


The API container waits until all three Ollama services are healthy before starting. Subsequent `docker-up` calls reuse cached weights and start in seconds.

**Developer / fresh-install fallback:** if you are not using the release bundles, Ollama containers will pull models on first run and you will need to seed the data separately — see [Judge quick start § Fallback](#judge-quick-start) and [Data pipeline](#data-pipeline).

---

## Running with Docker (recommended)

```bash
make docker-up       # docker compose --profile cpu-local up --build -d
make docker-stop     # docker compose --profile cpu-local stop ollama-generation ollama-judge ollama-embed backend frontend
make docker-start    # docker compose --profile cpu-local start ollama-generation ollama-judge ollama-embed backend frontend
make docker-down     # docker compose --profile cpu-local down
make docker-logs     # docker compose --profile cpu-local logs -f
make docker-shell    # docker exec -it backend-api bash
make docker-clean    # docker compose --profile cpu-local down -v
```

**Services and ports:**


| Container           | Host port | Purpose                                        |
| ------------------- | --------- | ---------------------------------------------- |
| `backend-api`       | 8000      | FastAPI application                            |
| `frontend-web`      | 5173      | React demo UI (nginx)                          |
| `ollama-generation` | 8001      | Agent inference — `qwen3:1.7b`                 |
| `ollama-judge`      | 8002      | Evaluation / LLM-as-judge — `deepseek-r1:1.5b` |
| `ollama-embed`      | 8003      | Text embeddings — `nomic-embed-text`           |


Rebuild only the backend after code changes:

```bash
docker compose --profile cpu-local up --build backend
```

---

## Running locally

### Backend

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/Mac
.venv\Scripts\activate           # Windows

# 2. Install dependencies
cd backend
pip install -r requirements.txt

# For the evaluation suite (adds bert-score, deepeval, datasets, etc.):
pip install -r requirements-eval.txt

# 3. Start Ollama and pull required models
ollama pull qwen3:1.7b
ollama pull deepseek-r1:1.5b
ollama pull nomic-embed-text
ollama serve                     # runs on localhost:11434

# 4. Configure environment (repo root)
cp .env.example .env
# For local Ollama, point all three URLs to the same instance:
#   OLLAMA_BASE_URL=http://localhost:11434
#   OLLAMA_JUDGE_URL=http://localhost:11434
#   OLLAMA_EMBED_URL=http://localhost:11434

# 5. Run the API
uvicorn src.main:app --reload --port 8000
# → http://localhost:8000/docs
```

---

## Frontend demo UI

The demo UI provides two pages:

- **Review** (`/review`) — submit a user ID and product details to call Task A and display the generated rating and review.
- **Recommend** (`/recommend`) — submit a user ID, context, and optional conversation history to call Task B and display recommendation cards with follow-up prompts.

Cold-start users are flagged with a badge when the backend detects no review history.

### Docker (default)

When using `make docker-up`, the UI is served at `http://localhost:5173` automatically — no separate dev server needed. The build reads `VITE_API_BASE_URL` from the repo-root `.env`.

### Local development

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

`VITE_API_BASE_URL` is read from the repo-root `.env` (see `.env.example`). Ensure the backend is running on that URL before testing API calls.

**Other scripts:**

```bash
npm run build        # Production build
npm run preview      # Preview production build locally
npm run test:run     # Vitest unit tests
npm run lint         # ESLint
```

---

## Data pipeline

> **Judges using release bundles can skip this section** — SQLite and all three ChromaDB collections are pre-seeded by `make judge-setup`.

Run once before making API calls if you are building from scratch. Each step saves output files that the next step reads from.

```bash
# From repo root (requires docker-up):
make pipeline
```

Or run steps individually inside the backend container (`make docker-shell`):

```bash
# Step 1: Download Amazon Books datasets from HuggingFace (~15% sample)
python -m data.pipeline.download --max-users 10000 --min-reviews 5
# Output: data/raw/reviews.jsonl, data/raw/metadata.jsonl

# Step 2: Merge reviews with item metadata
python -m data.pipeline.preprocess
# Output: data/processed/merged.parquet

# Step 3: Seed the relational database (SQLite at data/jollof.db)
python -m data.pipeline.seed_db
# Output: data/jollof.db

# Step 4: Convert reviews to natural language paragraphs (Task A RAG)
python -m data.pipeline.textualize
# Output: data/processed/textualized.parquet

# Step 5: Embed and index into ChromaDB — reviews collection (Task A RAG)
python -m data.pipeline.index --batch-size 512
# Output: data/chroma_db/

# Step 6: Textualize item descriptions (Task B items collection)
python -m data.pipeline.textualize_items
# Output: data/processed/textualized_items.parquet

# Step 7: Embed and index item descriptions into the items collection
python -m data.pipeline.index_items

# Step 8: Index review paragraphs into the user_reviews collection (Task B warm retrieval)
python -m data.pipeline.index --collection user_reviews
```

**ChromaDB collections:**


| Collection     | Populated by                  | Used by                         |
| -------------- | ----------------------------- | ------------------------------- |
| `reviews`      | `pipeline-index`              | Task A RAG retrieval            |
| `items`        | `pipeline-index-items`        | Task B item similarity search   |
| `user_reviews` | `pipeline-index-user-reviews` | Task B user vector construction |


> **Note:** Embeddings use `nomic-embed-text` (768-d vectors). If you switch embedding models, reset affected collections with `--reset` and re-run the index steps — vector dimensions must match.
>
> The relational DB (`data/jollof.db`) is seeded once via `seed_db` and kept up-to-date at runtime: Task A writes generated reviews back to the DB and ChromaDB automatically after each request.

---

## API reference

### Health check

```
GET /health
```

```json
{"status": "ok", "model": "qwen3:1.7b", "tasks": ["task-a", "task-b"]}
```

### Task A — simulate user review

```
POST /api/v1/task-a/generate-review
Content-Type: application/json
```

**Warm-start request (user history fetched from DB automatically):**

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

You may also pass `parent_asin` to look up item metadata from the catalogue (request fields override catalogue values):

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
  "review": "See ehn, this Achebe book na masterpiece no be lie...",
  "persona_summary": {
    "avg_rating": 4.0,
    "top_categories": ["Books > Literature & Fiction"],
    "tone": "concise",
    "sentiment_tendency": "positive",
    "cold_start": false
  }
}
```

**Cold-start** (user with no history in DB — detected automatically):

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

### Task B — get recommendations

```
POST /api/v1/task-b/recommend
Content-Type: application/json
```

**Warm-start request:**

```json
{
  "user_id": "AFKZENTNBQ7A7V7UXW5JJI6UGRYQ",
  "context": "Looking for something similar but set in modern Nigeria",
  "conversation": [],
  "top_k": 5
}
```

**Cold-start request (describe the user in `context`):**

```json
{
  "user_id": "NEW_USER_002",
  "context": "22-year-old Nigerian student who loves sci-fi and wants something thought-provoking but not too long",
  "conversation": [],
  "top_k": 5
}
```

**Multi-turn refinement:**

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
  "request_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "recommendations": [
    {
      "item_id": "B09BGPFTDB",
      "title": "Half of a Yellow Sun",
      "author": "Chimamanda Ngozi Adichie",
      "categories": "Books > Literature & Fiction > African Literature",
      "price": "13.49",
      "score": 0.94,
      "reason": "Abeg, if you liked Things Fall Apart, Half of a Yellow Sun go give you that same depth..."
    }
  ],
  "follow_up": "You prefer historical fiction or something set in present-day Nigeria?",
  "cold_start": false
}
```

Every Task B response includes a `request_id` for database verification.

---

## Verification API

Read-only endpoints for judges to confirm users, catalogue items, generated reviews, and recommendation runs exist in the database.


| Method | Path                                        | Description                                    |
| ------ | ------------------------------------------- | ---------------------------------------------- |
| `GET`  | `/api/v1/users/{user_id}`                   | User existence, review counts, cold-start flag |
| `GET`  | `/api/v1/users/{user_id}/reviews`           | Paginated review history (`?source=dataset     |
| `GET`  | `/api/v1/users/{user_id}/reviews/generated` | Task A write-backs only                        |
| `GET`  | `/api/v1/items/{parent_asin}`               | Catalogue item lookup                          |
| `POST` | `/api/v1/items/verify`                      | Batch ASIN verification                        |
| `GET`  | `/api/v1/users/{user_id}/recommendations`   | List persisted Task B runs                     |
| `GET`  | `/api/v1/recommendations/{request_id}`      | Full run + `catalogue_verified` per item       |


**Judge verification flow:**

```bash
# 1. Confirm user exists
curl http://localhost:8000/api/v1/users/AFKZENTNBQ7A7V7UXW5JJI6UGRYQ

# 2. Run Task B
curl -X POST http://localhost:8000/api/v1/task-b/recommend \
  -H "Content-Type: application/json" \
  -d '{"user_id":"AFKZENTNBQ7A7V7UXW5JJI6UGRYQ","context":"African fiction","top_k":3}'

# 3. Verify persisted run (use request_id from step 2)
curl http://localhost:8000/api/v1/recommendations/<request_id>

# 4. Confirm Task A output was written back
curl http://localhost:8000/api/v1/users/AFKZENTNBQ7A7V7UXW5JJI6UGRYQ/reviews/generated

# 5. Catalogue item lookup
curl http://localhost:8000/api/v1/items/0385474547
```

---

## Evaluation suite

```bash
make eval-generate   # refresh eval JSON (optional)
make eval-a          # Task A: ROUGE, BERTScore, BLEU, RMSE (+ fidelity requires ollama-judge)
make eval-b          # Task B: NDCG@10, Hit Rate@10, MRR, cold/warm subsets
make eval-all        # both suites
```

Or run directly from `backend/`:

```bash
python scripts/generate_eval_preds.py

python -m eval.suite \
  --task a \
  --preds data/eval/task_a_preds.json \
  --refs  data/eval/task_a_refs.json \
  --fidelity

python -m eval.suite \
  --task b \
  --preds data/eval/task_b_preds.json \
  --refs  data/eval/task_b_refs.json \
  --k 10
```

**DeepEval RAG metrics** (requires ollama-judge):

```bash
python -m eval.suite --task a --preds ... --refs ... --deepeval
```

Reports are written to `backend/eval/reports/` in JSON and Markdown formats.

---

## Environment variables

Copy `[.env.example](.env.example)` to `.env` at the **repo root**. Backend settings are loaded from that file whether you run via Docker or locally; `VITE_API_BASE_URL` is used by the frontend (Vite dev server and Docker build).


| Variable                         | Default                          | Description                                                |
| -------------------------------- | -------------------------------- | ---------------------------------------------------------- |
| `OLLAMA_BASE_URL`                | `http://ollama-generation:11434` | Ollama URL for agent inference (Task A & B)                |
| `AGENT_MODEL`                    | `qwen3:1.7b`                     | Agent LLM — generator                                      |
| `OLLAMA_JUDGE_URL`               | `http://ollama-judge:11434`      | Ollama URL for evaluation / LLM-as-judge                   |
| `JUDGE_MODEL`                    | `deepseek-r1:1.5b`               | Judge LLM (DeepEval, behavioural fidelity)                 |
| `OLLAMA_EMBED_URL`               | `http://ollama-embed:11434`      | Ollama URL for text embeddings                             |
| `EMBEDDING_MODEL`                | `nomic-embed-text`               | Ollama embedding model (768-d vectors)                     |
| `CHROMA_DB_PATH`                 | `data/chroma_db`                 | ChromaDB persistence directory                             |
| `CHROMA_COLLECTION`              | `reviews`                        | ChromaDB collection for Task A RAG                         |
| `CHROMA_ITEMS_COLLECTION`        | `items`                          | ChromaDB collection for Task B item search                 |
| `CHROMA_USER_REVIEWS_COLLECTION` | `user_reviews`                   | ChromaDB collection for Task B user vectors                |
| `RETRIEVAL_TOP_K`                | `10`                             | Default number of retrieved documents                      |
| `LLM_TEMPERATURE`                | `0.7`                            | Generation temperature                                     |
| `LLM_TOP_P`                      | `0.8`                            | Top-p nucleus sampling                                     |
| `LLM_MAX_TOKENS`                 | `512`                            | Default max new tokens                                     |
| `LOG_LEVEL`                      | `INFO`                           | Logging level                                              |
| `DATABASE_URL`                   | `sqlite:///data/jollof.db`       | Relational DB; use `postgresql+asyncpg://...` for Postgres |
| `VITE_API_BASE_URL`              | `http://localhost:8000`          | Frontend API base URL (local dev + Docker build)           |


---

## Datasets


| Dataset                              | Source                                                                                   | Usage                                    |
| ------------------------------------ | ---------------------------------------------------------------------------------------- | ---------------------------------------- |
| Amazon Reviews 2023 — Books Reviews  | [HuggingFace](https://huggingface.co/datasets/cogsci13/Amazon-Reviews-2023-Books-Review) | User review history, ratings, timestamps |
| Amazon Reviews 2023 — Books Metadata | [HuggingFace](https://huggingface.co/datasets/cogsci13/Amazon-Reviews-2023-Books-Meta)   | Item titles, authors, categories, prices |


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

## Technology stack


| Component     | Technology                          | Reason                                                                                           |
| ------------- | ----------------------------------- | ------------------------------------------------------------------------------------------------ |
| Agent LLM     | Qwen3:1.7b via Ollama               | Fast, naturalistic text; task-specific think/no-think modes                                      |
| Judge LLM     | DeepSeek-R1:1.5b via Ollama         | Reasoning model — better as evaluator than generator                                             |
| Embeddings    | nomic-embed-text via Ollama         | Served over HTTP — no PyTorch in the API image                                                   |
| Vector DB     | ChromaDB                            | File-local index at `data/chroma_db/`; metadata-filterable; no separate server                   |
| Relational DB | SQLite (aiosqlite)                  | Single file at `data/jollof.db`; audit + review persistence; swap to Postgres via `DATABASE_URL` |
| API Framework | FastAPI                             | Async, auto-docs, Pydantic validation                                                            |
| Frontend      | React + TypeScript + Vite           | Demo UI for Task A and Task B                                                                    |
| Evaluation    | ROUGE + BERTScore + BLEU + DeepEval | Covers all rubric metrics                                                                        |


---

## Solution paper

The solution paper is at `[SOLUTION_PAPER.md](SOLUTION_PAPER.md)` (repo root).

It covers problem framing, system architecture, Task A and Task B pipelines, evaluation methodology, ablation studies, and limitations.

---

## Judge quick start

Pre-packaged bundles (~3–4 GB models + demo data) let you skip the full pipeline entirely.

### Fast path (with submission bundles)

```bash
# 1. Clone and configure
git clone <repo-url>
cd jollof-intelligence
cp .env.example .env

# 2. Set bundle URLs (from GitHub Release attached to this submission)
#    Edit .env and fill in:
#      MODELS_BUNDLE_URL=<release-asset-url>
#      DEMO_DATA_BUNDLE_URL=<release-asset-url>

# 3. Download and extract models + demo data (~3–4 GB, one-time)
make judge-setup
# Without make:
cp -n .env.example .env
bash scripts/package_submission_assets.sh fetch-models
bash scripts/package_submission_assets.sh fetch-demo-data

# 4. Start the full stack (Ollama will be healthy in ~1–2 min — no model pull needed)
make docker-up
# Expected output when complete:
# ✓ API: http://localhost:8000/docs | UI: http://localhost:5173
# Without make:
docker compose --profile cpu-local up --build -d
# Then open:
#   API docs → http://localhost:8000/docs
#   Demo UI  → http://localhost:5173
```

No `make pipeline` needed — SQLite and all three ChromaDB collections (`reviews`, `items`, `user_reviews`) are pre-seeded in the bundle.

### Fallback (no bundles / fresh install)

```bash
cp .env.example .env
make docker-up    # pulls ~3–4 GB of Ollama models on first run
# Without make:
docker compose --profile cpu-local up --build -d

make pipeline     # 8-step pipeline: download, preprocess, seed, index
# Without make: run each pipeline step (see Data pipeline section)
```

### Disk and RAM requirements

- At least 8 GB free disk space (model weights across three Ollama containers)
- 8+ GB RAM recommended

---

## Sample workflow for judges

1. Run the [judge quick start](#judge-quick-start) above
2. Call Task A or B via `/docs` or the demo UI at `http://localhost:5173`
3. Verify outputs with the [Verification API](#verification-api) endpoints
4. Run `make eval-all` to reproduce metric reports

---

## Submission checklist (maintainers)

Before submitting, package the assets on a machine where `make pipeline` has completed:

```bash
# 1. Ensure models are pulled and pipeline is complete
make docker-up
make pipeline

# 2. Create bundles (output → dist/)
make package-submission

# 3. Upload dist/ollama_models.tar.gz and dist/demo_data.tar.gz to the GitHub Release

# 4. Paste the download URLs into .env.example:
#    MODELS_BUNDLE_URL=<url>
#    DEMO_DATA_BUNDLE_URL=<url>

# 5. Smoke-test the judge path
git clone <repo> /tmp/judge-test
cd /tmp/judge-test
cp .env.example .env
# Fill in bundle URLs, then:
make judge-setup && make docker-up
# Confirm /health, Task A, Task B, and verification API all respond correctly
```

