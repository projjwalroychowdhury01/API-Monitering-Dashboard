from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.logger import logger  # type: ignore
from app.routes import health
import app.routes.ingest as ingest
from app.kafka.simple_producer import create_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP
    app.state.producer = create_producer()
    yield
    # SHUTDOWN
    app.state.producer.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.SERVICE_NAME.replace("-", " ").title(),
        description=f"Service for {settings.SERVICE_NAME}",
        version="0.1.0",
        debug=settings.DEBUG,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(ingest.router)

    return app


app = create_app()