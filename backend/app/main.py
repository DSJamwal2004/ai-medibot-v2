"""
AI MediBot v2.2 — FastAPI Application Entry Point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.utils.logger import configure_logging, get_logger
from app.db.session import engine, Base

# Import all models so SQLAlchemy knows about them
import app.models  # noqa: F401

logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info("medibot_starting", version="2.2.0", env=settings.ENVIRONMENT)

    # Auto-create tables if they don't exist (idempotent)
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        Base.metadata.create_all(bind=engine)
    logger.info("database_tables_ready")

    yield

    logger.info("medibot_shutdown")


app = FastAPI(
    title="AI MediBot v2.2",
    description="Intelligent Medical Reasoning Assistant — structured, safe, explainable.",
    version="2.2.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ────────────────────────────────────────────────────────────────────
from app.api.v1 import auth, chat, conversations, health  # noqa: E402

app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(conversations.router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {"message": "AI MediBot v2.2", "docs": "/docs"}
