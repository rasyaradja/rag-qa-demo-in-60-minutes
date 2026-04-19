"""
API endpoints for running evaluation sets and fetching evaluation reports.

- POST /api/v1/eval/run: Trigger evaluation pipeline (admin-only in production).
- GET  /api/v1/eval/report: Fetch the latest evaluation report and metrics.

Uses services from backend.app.services.eval_service.
"""

import uuid
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession

from ....core.config import settings
from ....schemas.eval import (
    EvalRunRequest,
    EvalRunResponse,
    EvalReportOut,
    ErrorResponse,
)
from ....services.eval_service import (
    run_evaluation,
    get_latest_eval_report,
)
from ....db.session import get_db

router = APIRouter()

logger = logging.getLogger("eval_api")

def is_admin(request: Request) -> bool:
    """
    Placeholder for admin check.
    In production, implement authentication/authorization.
    For MVP/demo, allow all.
    """
    # Example: check for X-API-KEY or session
    # api_key = request.headers.get("x-api-key")
    # return api_key == settings.ADMIN_API_KEY
    return True

@router.post(
    "/eval/run",
    summary="Run evaluation set and generate report",
    tags=["evaluation"],
    response_model=EvalRunResponse,
    responses={
        200: {"model": EvalRunResponse},
        401: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def eval_run(
    req: EvalRunRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger the evaluation pipeline: runs the eval set through the RAG pipeline,
    scores answers, and writes a markdown report.

    Returns summary and per-question results.
    """
    # Admin-only in production
    if not is_admin(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to run evaluation.",
        )
    try:
        eval_set_id = None
        if req.eval_set_id:
            try:
                eval_set_id = uuid.UUID(str(req.eval_set_id))
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid eval_set_id format.",
                )
        result = await run_evaluation(
            db=db,
            eval_set_id=eval_set_id,
            prompt_version=req.prompt_version,
            llm_model=req.llm_model,
        )
        # Convert datetimes to isoformat for JSONResponse
        result["started_at"] = result["started_at"].isoformat()
        result["finished_at"] = result["finished_at"].isoformat()
        return JSONResponse(content=result, status_code=status.HTTP_200_OK)
    except Exception as e:
        logger.exception("Evaluation run failed.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation run failed: {e}",
        )

@router.get(
    "/eval/report",
    summary="Fetch latest evaluation report",
    tags=["evaluation"],
    response_model=EvalReportOut,
    responses={
        200: {"model": EvalReportOut},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def eval_report(
    eval_set_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Fetch the latest evaluation report, metrics, and per-question results.
    """
    try:
        eval_set_uuid = None
        if eval_set_id:
            try:
                eval_set_uuid = uuid.UUID(str(eval_set_id))
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid eval_set_id format.",
                )
        report = await get_latest_eval_report(db, eval_set_id=eval_set_uuid)
        # Convert datetime fields to isoformat for JSONResponse
        report_dict = report.dict()
        if hasattr(report.eval_set, "created_at") and report.eval_set.created_at:
            report_dict["eval_set"]["created_at"] = report.eval_set.created_at.isoformat()
        if hasattr(report, "generated_at") and report.generated_at:
            report_dict["generated_at"] = report.generated_at.isoformat()
        for r in report_dict.get("results", []):
            if "created_at" in r and r["created_at"]:
                r["created_at"] = r["created_at"].isoformat()
        return JSONResponse(content=report_dict, status_code=status.HTTP_200_OK)
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve),
        )
    except Exception as e:
        logger.exception("Failed to fetch evaluation report.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch evaluation report: {e}",
        )
