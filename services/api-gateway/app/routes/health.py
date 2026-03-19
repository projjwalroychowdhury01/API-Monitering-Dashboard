from fastapi import APIRouter
from app.config import settings

router = APIRouter()

@router.get("/health", tags=["System"])
async def health_check():
    """
    Standard health check endpoint.
    """
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0"
    }
