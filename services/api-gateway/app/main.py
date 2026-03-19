from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logging import logger
from app.routes import health

app = FastAPI(
    title="API Gateway",
    description="Central entry point for the API Observability Platform.",
    version="0.1.0",
    debug=settings.DEBUG
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(health.router)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Service {settings.SERVICE_NAME} started on port {settings.PORT}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Service {settings.SERVICE_NAME} shutting down...")
