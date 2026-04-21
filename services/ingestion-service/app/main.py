from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.dependencies import get_store
from app.logger import logger  # type: ignore
from app.routes import health
from app.routes import ingest
from app.kafka.simple_producer import create_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.producer = create_producer()
    get_store().ensure_schema()
    yield
    app.state.producer.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.SERVICE_NAME.replace("-", " ").title(),
        description="Normalized telemetry ingestion service",
        version="0.2.0",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(ingest.router)
    return app


app = create_app()
