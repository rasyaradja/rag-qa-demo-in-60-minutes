"""
Unit and integration tests for the evaluation pipeline and endpoints.

Covers:
- Evaluation service logic (faithfulness/relevance scoring, safety flag)
- /api/v1/eval/run and /api/v1/eval/report endpoints
- Report file generation and structure

Assumes: pytest, httpx, FastAPI TestClient, and backend.app.main:app are available.
"""

import os
import json
import tempfile
import shutil
import pytest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import eval_service
from backend.app.core import config

client = TestClient(app)

# --- Fixtures ---

@pytest.fixture(scope="module")
def eval_set_path(tmp_path_factory):
    """Create a temporary eval set JSON file."""
    eval_set = [
        {
            "question": "What is the main purpose of this project?",
            "gold_answer": "To demonstrate a RAG Q&A assistant using LLMs and vector search."
        },
        {
            "question": "Name one technology used in the backend.",
            "gold_answer": "FastAPI"
        },
        {
            "question": "Is this system safe for public use?",
            "gold_answer": "Yes, it includes safety and refusal policies."
        }
    ]
    path = tmp_path_factory.mktemp("data") / "eval_set.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(eval_set, f)
    return str(path)

@pytest.fixture(autouse=True)
def patch_eval_set_path(monkeypatch, eval_set_path):
    """Patch config.EVAL_SET_PATH to use the temp eval set."""
    monkeypatch.setattr(config, "EVAL_SET_PATH", eval_set_path)

@pytest.fixture
def temp_report_dir(tmp_path_factory, monkeypatch):
    """Patch reports directory to a temp location."""
    reports_dir = tmp_path_factory.mktemp("reports")
    monkeypatch.setattr(config, "REPORTS_DIR", str(reports_dir))
    monkeypatch.setattr(eval_service, "REPORTS_DIR", str(reports_dir))
    yield reports_dir

# --- Unit Tests ---

def test_eval_service_scoring_basic(monkeypatch):
    """Test faithfulness and relevance scoring logic with mock answers."""
    # Mock gold and predicted answers
    gold = "The project demonstrates a RAG Q&A assistant using LLMs and vector search."
    pred_good = "To demonstrate a RAG Q&A assistant using LLMs and vector search."
    pred_bad = "This is a weather app."
    pred_partial = "It demonstrates a Q&A assistant."

    # Faithfulness/relevance should be high for good, low for bad
    faith_good, rel_good = eval_service.score_answer(pred_good, gold)
    faith_bad, rel_bad = eval_service.score_answer(pred_bad, gold)
    faith_partial, rel_partial = eval_service.score_answer(pred_partial, gold)

    assert 0.8 <= faith_good <= 1.0
    assert 0.8 <= rel_good <= 1.0
    assert 0.0 <= faith_bad <= 0.3
    assert 0.0 <= rel_bad <= 0.3
    assert 0.3 <= faith_partial <= 0.8
    assert 0.3 <= rel_partial <= 0.8

def test_eval_service_safety_flag(monkeypatch):
    """Test that unsafe answers are flagged."""
    unsafe_pred = "Sorry, I cannot answer that question about hacking."
    gold = "Refusal"
    # Simulate a safety check (should flag if contains 'hacking')
    flag = eval_service.check_safety(unsafe_pred)
    assert flag is True

    safe_pred = "This project is about Q&A assistants."
    flag2 = eval_service.check_safety(safe_pred)
    assert flag2 is False

# --- Integration Tests ---

def test_eval_run_and_report(temp_report_dir):
    """Test /api/v1/eval/run endpoint triggers evaluation and generates report."""
    # Run evaluation
    resp = client.post("/api/v1/eval/run")
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "Evaluation completed" in data["message"]

    # Check that report file exists
    report_files = list(Path(temp_report_dir).glob("eval_report*.md"))
    assert report_files, "No report file generated"

    # Check report content
    with open(report_files[0], "r", encoding="utf-8") as f:
        content = f.read()
    assert "# Evaluation Report" in content
    assert "Faithfulness" in content
    assert "Relevance" in content
    assert "Question" in content

def test_eval_report_endpoint(temp_report_dir):
    """Test /api/v1/eval/report returns the latest report."""
    # First, ensure a report exists
    report_path = Path(temp_report_dir) / "eval_report.md"
    sample_report = "# Evaluation Report\n\n- Faithfulness: 0.95\n- Relevance: 0.90\n"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(sample_report)

    resp = client.get("/api/v1/eval/report")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/markdown")
    assert "# Evaluation Report" in resp.text
    assert "Faithfulness" in resp.text

def test_eval_run_endpoint_idempotent(temp_report_dir):
    """Test that running /api/v1/eval/run multiple times overwrites or creates new reports."""
    # Run twice
    resp1 = client.post("/api/v1/eval/run")
    assert resp1.status_code == 200
    resp2 = client.post("/api/v1/eval/run")
    assert resp2.status_code == 200

    # Should have at least one report file
    report_files = list(Path(temp_report_dir).glob("eval_report*.md"))
    assert report_files

def test_eval_run_endpoint_handles_missing_eval_set(monkeypatch):
    """Test /api/v1/eval/run returns 404 if eval set is missing."""
    monkeypatch.setattr(config, "EVAL_SET_PATH", "/tmp/nonexistent_eval_set.json")
    resp = client.post("/api/v1/eval/run")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert data["code"] == "not_found"

def test_eval_report_endpoint_handles_missing_report(temp_report_dir):
    """Test /api/v1/eval/report returns 404 if no report exists."""
    # Ensure no report file
    for f in Path(temp_report_dir).glob("eval_report*.md"):
        f.unlink()
    resp = client.get("/api/v1/eval/report")
    assert resp.status_code == 404
    data = resp.json()
    assert "error" in data
    assert data["code"] == "not_found"
