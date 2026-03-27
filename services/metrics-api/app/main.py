import os
import traceback
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Metrics API",
    description="API for fetching observability metrics",
    version="1.0.0"
)

# Enforce secure CORS policy: whitelist only trusted domains from environment
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Include the metrics router — surface import errors immediately
try:
    from app.routes.metrics import router as metrics_router
    app.include_router(metrics_router)
except Exception:
    # Print full traceback so the cause is visible in the uvicorn terminal
    traceback.print_exc()
    raise RuntimeError(
        "Failed to load metrics router. "
        "Check the traceback above for the root cause."
    )

@app.get("/health")
async def health_check():
    return {
        "status": "success",
        "data": {
            "status": "healthy"
        }
    }
