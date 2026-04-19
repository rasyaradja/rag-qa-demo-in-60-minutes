"""
FastAPI application entry point for RAG Q&A Demo.

- Loads settings and configures CORS.
- Registers API routers for RAG, evaluation, and health endpoints.
- Sets up exception handlers and OpenAPI metadata.
- Ready for use with ASGI servers (uvicorn/gunicorn).
"""

import logging
import sys

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.config import settings

# Import API routers
from .api.v1.endpoints.rag import router as rag_router
from .api.v1.endpoints.eval import router as eval_router
from .api.v1.endpoints.health import router as health_router

# --- Logging setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("main")

# --- FastAPI app instance ---
app = FastAPI(
    title="RAG Q&A Demo",
    description="Retrieval-Augmented Generation Q&A assistant demo with evaluation pipeline.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# --- CORS middleware ---
origins = settings.ALLOWED_ORIGINS or ["*"]
if isinstance(origins, str):
    origins = [o.strip() for o in origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Exception handlers ---

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "internal_error"},
    )

# --- API Routers ---
app.include_router(
    rag_router,
    prefix="/api/v1",
    tags=["rag"],
)
app.include_router(
    eval_router,
    prefix="/api/v1",
    tags=["evaluation"],
)
app.include_router(
    health_router,
    prefix="/api/v1",
    tags=["health"],
)

# --- Root endpoint ---

@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint: basic info and health check.
    """
    return {
        "service": "RAG Q&A Demo",
        "status": "ok",
        "version": app.version,
        "docs_url": app.docs_url,
        "api_base": "/api/v1",
    }
