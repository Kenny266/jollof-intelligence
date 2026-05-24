"""
Jollof Intelligence — Unified FastAPI Application
DSN x BCT LLM Agent Challenge — Hackathon 3.0

Serves both Task A (User Modeling) and Task B (Recommendation) under one API.
"""
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.db.engine import init_db
from src.config import get_settings
from src.router.user_modelling_router import router as task_a_router
from src.router.recommender_router import router as task_b_router
from src.router.verification_router import router as verification_router

logging.basicConfig(
    stream=sys.stdout,
    level=getattr(logging, get_settings().log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Jollof Intelligence starting up — Ollama: %s | Model: %s",
        settings.ollama_base_url,
        settings.agent_model,
    )
    await init_db()
    logger.info("Relational DB initialised at %s", settings.database_url)
    yield
    logger.info("Jollof Intelligence shutting down")


app = FastAPI(
    title="Jollof Intelligence API",
    description=(
        "LLM Agent pipelines for the DSN x BCT Hackathon 3.0.\n\n"
        "**Task A** — User Modeling: Simulate authentic Nigerian-English reviews and "
        "star ratings for unseen items.\n\n"
        "**Task B** — Recommendation: Personalized book recommendations with cold-start, "
        "cross-domain reasoning, and multi-turn dialogue support."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(task_a_router, prefix="/api/v1")
app.include_router(task_b_router, prefix="/api/v1")
app.include_router(verification_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check():
    settings = get_settings()
    return JSONResponse({
        "status": "ok",
        "ollama_url": settings.ollama_base_url,
        "model": settings.agent_model,
        "tasks": ["task-a", "task-b"],
    })


@app.get("/", include_in_schema=False)
async def root():
    return JSONResponse({
        "message": "Jollof Intelligence API is running.",
        "docs": "/docs",
        "health": "/health",
    })
