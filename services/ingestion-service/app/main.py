from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.logger import logger #type: ignore
from app.routes import health, ingest


def create_app() -> FastAPI:
    """
    App factory to initialize FastAPI with common middleware and routes.
    """

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # 🔹 STARTUP
        logger.info( #type: ignore
            "Service starting",
            extra={"service": settings.SERVICE_NAME}
        )

        # Future: initialize Kafka producer here
        # app.state.producer = init_producer()

        yield

        # 🔹 SHUTDOWN
        logger.info( #type: ignore
            "Service shutting down",
            extra={"service": settings.SERVICE_NAME}
        )

        # Future: close Kafka producer here
        # app.state.producer.close()

    app = FastAPI(
        title=settings.SERVICE_NAME.replace("-", " ").title(),
        description=f"Service for {settings.SERVICE_NAME}",
        version="0.1.0",
        debug=settings.DEBUG,
        lifespan=lifespan   # ✅ FIX HERE
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health.router)
    app.include_router(ingest.router)

    return app


app = create_app()