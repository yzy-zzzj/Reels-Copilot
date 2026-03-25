"""
FastAPI application entry point.
"""
from __future__ import annotations

import logging

import redis as redis_lib
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app import config
from app.webhook import router as webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = redis_lib.from_url(config.REDIS_URL, decode_responses=True)
    logger.info("Redis connected: %s", config.REDIS_URL)
    yield
    app.state.redis.close()


app = FastAPI(title="Reels Copilot", lifespan=lifespan)
app.include_router(webhook_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
