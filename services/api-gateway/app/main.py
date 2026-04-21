from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.dependencies import get_store
from app.logging import logger
from app.routes import health
from app.routes.v1 import router as control_plane_router


app = FastAPI(
    title="API Gateway",
    description="Control-plane API for the observability platform.",
    version="0.2.0",
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(control_plane_router)


@app.on_event("startup")
async def startup_event():
    get_store().ensure_schema()
    logger.info(f"Service {settings.SERVICE_NAME} started on port {settings.PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Service {settings.SERVICE_NAME} shutting down...")
