import traceback

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.dependencies import get_store
from app.routes.health import router as health_router
from app.routes.metrics import router as metrics_router
from app.routes.platform import router as platform_router


app = FastAPI(
    title="Metrics API",
    description="Query-plane API for observability metrics, traces, and incidents.",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

try:
    get_store().ensure_schema()
    app.include_router(health_router)
    app.include_router(metrics_router)
    app.include_router(platform_router)
except Exception:
    traceback.print_exc()
    raise RuntimeError("Failed to load metrics/query routers. Check the traceback above for the root cause.")
