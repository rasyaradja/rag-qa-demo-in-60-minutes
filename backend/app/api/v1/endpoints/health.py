"""
Health check endpoint for FastAPI backend.

- GET /api/v1/rag/health
- Returns {"status": "ok"} if backend is running.
- Used for readiness/liveness probes and frontend API checks.
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get(
    "/health",
    summary="Health check",
    tags=["health"],
    response_model=dict,
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """
    Simple health check endpoint.
    Returns 200 OK with {"status": "ok"} if backend is running.
    """
    return JSONResponse(content={"status": "ok"}, status_code=status.HTTP_200_OK)
