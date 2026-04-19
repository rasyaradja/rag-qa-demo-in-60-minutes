"""
Service for running evaluation sets and scoring RAG answers.

- Loads evaluation sets (20 Q&A pairs) from DB or file.
- Runs each question through the RAG pipeline, capturing answer, citations, latency, and cost.
- Scores faithfulness (does answer align with retrieved sources?) and relevance (does answer address the question?).
- Flags unsafe or refused answers.
- Aggregates metrics and writes a markdown report.
- Persists results to DB and returns structured API responses.

This module is used by the /api/v1/eval/run and /api/v1/eval/report endpoints.
"""

import os
import uuid
import time
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert

from ..core.config import settings
from ..core.prompts import get_prompt_template, get_prompt_version
from ..core.llm import get_llm_client
from ..core.embeddings import get_embedding_model
from ..core.vectorstore import get_vectorstore
from ..models.eval import EvalSet, EvalResult
from ..models.query import UserQuery
from ..schemas.eval import (
    EvalQuestion,
    EvalSetOut,
    EvalResultOut,
    EvalReportOut,
    EvalReportMetrics,
)
from ..schemas.rag import RAGAnswerOut
from .rag_service import answer_question_rag

logger = logging.getLogger("eval_service")

# --- Faithfulness & Relevance Scoring ---

def score_faithfulness(answer: Optional[str], citations: List[Dict[str, Any]], gold_answer: Optional[str]) -> float:
    """
    Naive faithfulness scoring:
    - 1.0 if answer is empty/refused (safe default)
    - 1.0 if answer is a substring of any citation chunk
    - 0.5 if answer overlaps with any citation chunk (token overlap > 30%)
    - 0.0 otherwise
    """
    if not answer:
        return 1.0
    answer_lc = answer.lower()
    for c in citations:
        chunk = (c.get("chunk") or c.get("title") or "").lower()
        if answer_lc in chunk or chunk in answer_lc:
            return 1.0
        # Token overlap
        a_tokens = set(answer_lc.split())
        c_tokens = set(chunk.split())
        if a_tokens and c_tokens:
            overlap = len(a_tokens & c_tokens) / max(len(a_tokens), 1)
            if overlap > 0.3:
                return 0.5
    # If gold answer is provided, check overlap
    if gold_answer:
        gold_lc = gold_answer.lower()
        if gold_lc in answer_lc or answer_lc in gold_lc:
            return 1.0
    return 0.0

def score_relevance(answer: Optional[str], question: str, gold_answer: Optional[str]) -> float:
    """
    Naive relevance scoring:
    - 1.0 if answer is non-empty and not a refusal
    - 0.5 if answer is generic or partial (length < 20 chars)
    - 0.0 if answer is empty or refused
    """
    if not answer or answer.strip() == "":
        return 0.0
    if "refus" in answer.lower() or "cannot answer" in answer.lower():
        return 0.0
    if len(answer.strip()) < 20:
        return 0.5
    # If gold answer is provided, check overlap
    if gold_answer:
        gold_lc = gold_answer.lower()
        answer_lc = answer.lower()
        if gold_lc in answer_lc or answer_lc in gold_lc:
            return 1.0
    return 1.0

def is_unsafe_or_refused(status: str, answer: Optional[str]) -> bool:
    """
    Returns True if the answer was refused or flagged unsafe.
    """
    if status == "refused":
        return True
    if answer and ("unsafe" in answer.lower() or "not allowed" in answer.lower()):
        return True
    return False

# --- Evaluation Pipeline ---

async def load_eval_set(
    db: AsyncSession,
    eval_set_id: Optional[uuid.UUID] = None,
    eval_set_path: Optional[str] = None,
) -> Tuple[EvalSet, List[EvalQuestion]]:
    """
    Loads the evaluation set from DB or file.
    """
    if eval_set_id:
        stmt = select(EvalSet).where(EvalSet.id == eval_set_id)
        result = await db.execute(stmt)
        eval_set = result.scalar_one_or_none()
        if not eval_set:
            raise ValueError(f"EvalSet not found: {eval_set_id}")
        questions = eval_set.questions or []
        return eval_set, [EvalQuestion(**q) for q in questions]
    # Load from file (JSON)
    path = eval_set_path or settings.EVAL_SET_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"Eval set file not found: {path}")
    import json
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    name = data.get("name", "Default Eval Set")
    questions = [EvalQuestion(**q) for q in data["questions"]]
    # Insert into DB if not exists
    stmt = select(EvalSet).where(EvalSet.name == name)
    result = await db.execute(stmt)
    eval_set = result.scalar_one_or_none()
    if not eval_set:
        eval_set = EvalSet(
            id=uuid.uuid4(),
            name=name,
            questions=[q.dict() for q in questions],
            created_at=datetime.now(timezone.utc),
        )
        db.add(eval_set)
        await db.commit()
    return eval_set, questions

async def run_evaluation(
    db: AsyncSession,
    eval_set_id: Optional[uuid.UUID] = None,
    prompt_version: Optional[str] = None,
    llm_model: Optional[str] = None,
    eval_set_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Runs the evaluation set through the RAG pipeline, scores answers, and writes a markdown report.

    Returns:
        {
            "eval_set_id": ...,
            "num_questions": ...,
            "started_at": ...,
            "finished_at": ...,
            "report_path": ...,
            "results": [EvalResultOut, ...]
        }
    """
    started_at = datetime.now(timezone.utc)
    eval_set, questions = await load_eval_set(db, eval_set_id, eval_set_path)
    logger.info(f"Running evaluation: {eval_set.name} ({len(questions)} questions)")

    results: List[EvalResult] = []
    rag_results: List[RAGAnswerOut] = []
    total_latency = 0.0
    total_cost = 0.0
    num_safe = 0
    num_unsafe = 0
    faithfulness_scores = []
    relevance_scores = []

    for idx, q in enumerate(questions):
        logger.info(f"Evaluating Q{idx+1}: {q.question[:80]}...")
        t0 = time.perf_counter()
        # Run through RAG pipeline
        rag_out: RAGAnswerOut = await answer_question_rag(
            db=db,
            question=q.question,
            prompt_version=prompt_version,
            llm_model=llm_model,
            eval_mode=True,
        )
        t1 = time.perf_counter()
        latency_ms = int((t1 - t0) * 1000)
        cost_usd = getattr(rag_out, "cost_usd", None) or 0.0

        # Score
        faithfulness = score_faithfulness(
            rag_out.answer, [c.dict() for c in rag_out.citations], q.gold_answer
        )
        relevance = score_relevance(rag_out.answer, q.question, q.gold_answer)
        safety_flag = is_unsafe_or_refused(rag_out.status, rag_out.answer)

        if safety_flag:
            num_unsafe += 1
        else:
            num_safe += 1
        faithfulness_scores.append(faithfulness)
        relevance_scores.append(relevance)
        total_latency += latency_ms
        total_cost += cost_usd

        # Persist UserQuery and EvalResult
        user_query = UserQuery(
            id=rag_out.id,
            question=rag_out.question,
            answer=rag_out.answer,
            citations=[c.document_id for c in rag_out.citations],
            created_at=rag_out.created_at,
            status=rag_out.status,
            llm_model=rag_out.llm_model,
            prompt_version=rag_out.prompt_version,
        )
        db.add(user_query)
        await db.flush()

        eval_result = EvalResult(
            id=uuid.uuid4(),
            eval_set_id=eval_set.id,
            query_id=user_query.id,
            faithfulness=faithfulness,
            relevance=relevance,
            safety_flag=safety_flag,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            created_at=datetime.now(timezone.utc),
        )
        db.add(eval_result)
        await db.commit()

        results.append(eval_result)
        rag_results.append(rag_out)

    finished_at = datetime.now(timezone.utc)
    avg_faithfulness = (
        sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else None
    )
    avg_relevance = (
        sum(relevance_scores) / len(relevance_scores) if relevance_scores else None
    )
    avg_latency_ms = total_latency / len(questions) if questions else None

    # Write markdown report
    report_path = await write_eval_report(
        eval_set=eval_set,
        questions=questions,
        rag_results=rag_results,
        eval_results=results,
        metrics={
            "avg_faithfulness": avg_faithfulness,
            "avg_relevance": avg_relevance,
            "num_safe": num_safe,
            "num_unsafe": num_unsafe,
            "avg_latency_ms": avg_latency_ms,
            "total_cost_usd": total_cost,
        },
        started_at=started_at,
        finished_at=finished_at,
        prompt_version=prompt_version or get_prompt_version(),
        llm_model=llm_model or settings.LLM_MODEL,
    )

    # Prepare API response
    from ..schemas.eval import EvalResultOut
    result_outs = [
        EvalResultOut(
            id=r.id,
            created_at=r.created_at,
            eval_set_id=r.eval_set_id,
            query_id=r.query_id,
            faithfulness=r.faithfulness,
            relevance=r.relevance,
            safety_flag=r.safety_flag,
            latency_ms=r.latency_ms,
            cost_usd=r.cost_usd,
        )
        for r in results
    ]

    return {
        "eval_set_id": str(eval_set.id),
        "num_questions": len(questions),
        "started_at": started_at,
        "finished_at": finished_at,
        "report_path": report_path,
        "results": result_outs,
    }

async def write_eval_report(
    eval_set: EvalSet,
    questions: List[EvalQuestion],
    rag_results: List[RAGAnswerOut],
    eval_results: List[EvalResult],
    metrics: Dict[str, Any],
    started_at: datetime,
    finished_at: datetime,
    prompt_version: Optional[str],
    llm_model: Optional[str],
) -> str:
    """
    Writes a markdown evaluation report to reports/eval_report.md.
    """
    report_dir = os.path.join(settings.REPORTS_PATH or "reports")
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, "eval_report.md")
    dt_str = finished_at.strftime("%Y-%m-%d %H:%M:%S UTC")

    lines = []
    lines.append(f"# Evaluation Report")
    lines.append(f"**Eval Set:** {eval_set.name}")
    lines.append(f"**Prompt Version:** `{prompt_version}`")
    lines.append(f"**LLM Model:** `{llm_model}`")
    lines.append(f"**Run Time:** {dt_str}")
    lines.append(f"**Questions Evaluated:** {len(questions)}")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append(f"- Average Faithfulness: `{metrics.get('avg_faithfulness'):.2f}`")
    lines.append(f"- Average Relevance: `{metrics.get('avg_relevance'):.2f}`")
    lines.append(f"- Safe Answers: `{metrics.get('num_safe')}`")
    lines.append(f"- Unsafe/Refused: `{metrics.get('num_unsafe')}`")
    lines.append(f"- Average Latency: `{metrics.get('avg_latency_ms'):.0f} ms`")
    lines.append(f"- Total API Cost: `${metrics.get('total_cost_usd'):.4f}`")
    lines.append("")
    lines.append("## Per-Question Results")
    lines.append("")
    for idx, (q, rag, res) in enumerate(zip(questions, rag_results, eval_results)):
        lines.append(f"### Q{idx+1}: {q.question}")
        lines.append(f"- **Gold Answer:** {q.gold_answer or '_N/A_'}")
        lines.append(f"- **Model Answer:** {rag.answer or '_No answer_'}")
        lines.append(f"- **Citations:** {', '.join([c.title or str(c.document_id) for c in rag.citations]) or '_None_'}")
        lines.append(f"- **Status:** {rag.status}")
        lines.append(f"- **Faithfulness:** `{res.faithfulness}`")
        lines.append(f"- **Relevance:** `{res.relevance}`")
        lines.append(f"- **Safety Flag:** `{res.safety_flag}`")
        lines.append(f"- **Latency:** `{res.latency_ms} ms`")
        lines.append(f"- **Cost:** `${res.cost_usd:.4f}`")
        lines.append("")
    lines.append("---")
    lines.append(f"_Report generated at {dt_str}_")

    async with await aio_open(report_path, "w", encoding="utf-8") as f:
        await f.write("\n".join(lines))
    logger.info(f"Evaluation report written to: {report_path}")
    return report_path

# --- Utility for async file write (aiofiles) ---

try:
    import aiofiles
    aio_open = aiofiles.open
except ImportError:
    # Fallback to sync open for environments without aiofiles (should not happen in prod)
    import builtins
    async def aio_open(*args, **kwargs):
        return builtins.open(*args, **kwargs)

# --- Fetch Latest Report ---

async def get_latest_eval_report(
    db: AsyncSession,
    eval_set_id: Optional[uuid.UUID] = None,
) -> EvalReportOut:
    """
    Loads the latest evaluation report and results from DB and markdown file.
    """
    # Get latest EvalSet
    if eval_set_id:
        stmt = select(EvalSet).where(EvalSet.id == eval_set_id)
    else:
        stmt = select(EvalSet).order_by(EvalSet.created_at.desc())
    result = await db.execute(stmt)
    eval_set = result.scalar_one_or_none()
    if not eval_set:
        raise ValueError("No evaluation set found.")

    # Get all EvalResults for this set
    stmt = select(EvalResult).where(EvalResult.eval_set_id == eval_set.id)
    result = await db.execute(stmt)
    eval_results = result.scalars().all()

    # Aggregate metrics
    faithfulness_scores = [r.faithfulness for r in eval_results if r.faithfulness is not None]
    relevance_scores = [r.relevance for r in eval_results if r.relevance is not None]
    num_safe = sum(1 for r in eval_results if not r.safety_flag)
    num_unsafe = sum(1 for r in eval_results if r.safety_flag)
    avg_latency_ms = (
        sum(r.latency_ms for r in eval_results if r.latency_ms is not None) / len(eval_results)
        if eval_results else None
    )
    total_cost_usd = sum(r.cost_usd or 0.0 for r in eval_results)
    avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else None
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else None

    # Find report file
    report_path = os.path.join(settings.REPORTS_PATH or "reports", "eval_report.md")
    generated_at = None
    if os.path.exists(report_path):
        generated_at = datetime.fromtimestamp(os.path.getmtime(report_path), tz=timezone.utc)
    else:
        generated_at = datetime.now(timezone.utc)

    # Prepare schemas
    from ..schemas.eval import EvalSetOut, EvalResultOut, EvalReportMetrics, EvalReportOut
    eval_set_out = EvalSetOut(
        id=eval_set.id,
        created_at=eval_set.created_at,
        name=eval_set.name,
        questions=[EvalQuestion(**q) for q in eval_set.questions],
    )
    result_outs = [
        EvalResultOut(
            id=r.id,
            created_at=r.created_at,
            eval_set_id=r.eval_set_id,
            query_id=r.query_id,
            faithfulness=r.faithfulness,
            relevance=r.relevance,
            safety_flag=r.safety_flag,
            latency_ms=r.latency_ms,
            cost_usd=r.cost_usd,
        )
        for r in eval_results
    ]
    metrics = EvalReportMetrics(
        avg_faithfulness=avg_faithfulness,
        avg_relevance=avg_relevance,
        num_safe=num_safe,
        num_unsafe=num_unsafe,
        avg_latency_ms=avg_latency_ms,
        total_cost_usd=total_cost_usd,
    )
    return EvalReportOut(
        eval_set=eval_set_out,
        metrics=metrics,
        results=result_outs,
        report_path=report_path,
        generated_at=generated_at,
        prompt_version=get_prompt_version(),
        llm_model=settings.LLM_MODEL,
    )
