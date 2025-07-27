"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """API health check."""
    return {"status": "healthy", "service": "api"}


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    # TODO: Add database connectivity check
    return {"status": "ready"}