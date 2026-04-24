from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logger import logger
from app.routes import health

def create_app() -> FastAPI:
    """
    App factory to initialize FastAPI with common middleware and routes.
    """
    app = FastAPI(
        title=settings.SERVICE_NAME.replace("-", " ").title(),
        description=f"Service for {settings.SERVICE_NAME}",
        version="0.1.0",
        debug=settings.DEBUG
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register standardized routes
    app.include_router(health.router)

    @app.on_event("startup")
    async def startup():
        logger.info(f"Service {settings.SERVICE_NAME} starting...")

    @app.on_event("shutdown")
    async def shutdown():
        logger.info(f"Service {settings.SERVICE_NAME} shutting down...")

    return app

app = create_app()
