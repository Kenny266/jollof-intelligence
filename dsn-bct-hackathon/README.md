# DSN × BCT LLM Agent Challenge

> **Team submission** — Data & AI Summit Hackathon 3.0  
> Deadline: 24 May 2026

Two LLM-powered agents that model human behaviour and deliver personalised recommendations from review data.

---

## Repo structure

```
dsn-bct-hackathon/
├── task_a/              # User Modeling agent
│   ├── app/             # FastAPI application
│   ├── prompts/         # LLM prompt templates
│   ├── eval/            # ROUGE / BERTScore / RMSE evaluation
│   └── Dockerfile
├── task_b/              # Recommendation agent
│   ├── app/             # FastAPI application
│   ├── prompts/         # LLM prompt templates
│   ├── eval/            # NDCG@10 / Hit Rate evaluation
│   └── Dockerfile
├── shared/              # Shared modules
│   ├── llm/             # LLM client + Nigerian context injector
│   ├── persona/         # Persona builder from review history
│   └── retrieval/       # RAG pipeline + FAISS vector store
├── data/
│   ├── raw/             # Downloaded datasets (gitignored)
│   └── processed/       # Cleaned + indexed data
├── notebooks/           # EDA and exploration
├── scripts/             # Data download + eval runner
├── paper/               # Solution paper (PDF)
├── docker-compose.yml
└── requirements.txt
```

---

## Quickstart

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Download datasets
```bash
bash scripts/download_data.sh
```

### 3. Run Task A locally
```bash
cd task_a
uvicorn app.main:app --reload --port 8000
```

### 4. Run Task B locally
```bash
cd task_b
uvicorn app.main:app --reload --port 8001
```

### 5. Run both via Docker
```bash
docker-compose up --build
```

---

## API reference

### Task A — POST /generate-review
Request:
```json
{
  "user_id": "U123",
  "user_history": [],
  "product": { "name": "Jollof Rice", "category": "Food", "location": "Lagos" }
}
```
Response:
```json
{ "rating": 4, "review": "Honestly, this jollof rice no get rival..." }
```

### Task B — POST /recommend
Request:
```json
{
  "user_id": "U123",
  "user_history": [],
  "context": "Looking for a nice spot for owambe this weekend",
  "conversation": []
}
```
Response:
```json
{
  "recommendations": [
    { "item_id": "B001", "name": "...", "score": 0.94, "reason": "..." }
  ]
}
```

---

## Evaluation
```bash
bash scripts/run_eval.sh
```
Runs ROUGE-L, BERTScore, RMSE for Task A; NDCG@10 and Hit Rate for Task B.

---

## Datasets
- Yelp Open Dataset: https://www.yelp.com/dataset
- Amazon Reviews 2023: https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023
- UCSD Goodreads: https://mengtingwan.github.io/data/goodreads.html

---

## Team
- Engineer A — Data pipeline, Task A, evaluation
- Engineer B — Infra, Task B, Docker, README
