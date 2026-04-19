"""
Tests for the RAG pipeline and question answering endpoint.

Covers:
- /api/v1/rag/answer endpoint: normal, refusal, error, and citation extraction
- RAG service: embedding, retrieval, prompt construction, LLM call, safety/refusal logic
- Input validation and error handling
- Citation structure and content

Assumes: pytest, FastAPI TestClient, backend.app.main:app, and backend.app.services.rag_service are available.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services import rag_service

client = TestClient(app)

# --- Fixtures and Mocks ---

@pytest.fixture(autouse=True)
def patch_rag_service(monkeypatch):
    """
    Patch rag_service methods to avoid real LLM/vector DB calls.
    """
    # Mock embedding
    monkeypatch.setattr(rag_service, "embed_question", lambda q: [0.1, 0.2, 0.3])

    # Mock retrieval: always return two fake docs
    class FakeDoc:
        def __init__(self, id, title, content, source_url=None):
            self.id = id
            self.title = title
            self.content = content
            self.source_url = source_url

    def fake_retrieve(embedding, top_k=3):
        return [
            FakeDoc(
                id="doc1",
                title="Project Overview",
                content="This project demonstrates a RAG Q&A assistant using LLMs and vector search.",
                source_url="https://example.com/project"
            ),
            FakeDoc(
                id="doc2",
                title="Backend Tech",
                content="The backend uses FastAPI and SQLAlchemy.",
                source_url=None
            ),
        ]
    monkeypatch.setattr(rag_service, "retrieve_documents", fake_retrieve)

    # Mock prompt construction: just join context and question
    monkeypatch.setattr(rag_service, "construct_prompt", lambda q, ctx, v: f"{ctx}\nQ: {q}")

    # Mock LLM call: return canned answers based on question
    def fake_llm_call(prompt, model, **kwargs):
        if "unsafe" in prompt.lower():
            return "Sorry, I cannot answer that question."
        if "weather" in prompt.lower():
            return "I'm sorry, I can only answer questions about the project documents."
        if "backend" in prompt.lower():
            return "The backend uses FastAPI and SQLAlchemy. [doc2]"
        return "This project demonstrates a RAG Q&A assistant using LLMs and vector search. [doc1]"
    monkeypatch.setattr(rag_service, "call_llm", fake_llm_call)

    # Mock citation extraction: extract [docX] tags
    def fake_extract_citations(answer, retrieved_docs):
        import re
        ids = re.findall(r"\[(doc\d+)\]", answer)
        return [
            {
                "id": doc.id,
                "title": doc.title,
                "source_url": doc.source_url,
                "snippet": doc.content[:60]
            }
            for doc in retrieved_docs if doc.id in ids
        ]
    monkeypatch.setattr(rag_service, "extract_citations", fake_extract_citations)

    # Mock safety/refusal check
    def fake_check_refusal(question):
        if "unsafe" in question.lower() or "hack" in question.lower():
            return True, "Refused due to safety policy."
        if "weather" in question.lower():
            return True, "Out of scope: only project-related questions allowed."
        return False, None
    monkeypatch.setattr(rag_service, "check_refusal", fake_check_refusal)

# --- Tests for /api/v1/rag/answer ---

def test_answer_success_with_citations():
    """Test normal question returns answer and citations."""
    payload = {"question": "What does this project do?"}
    resp = client.post("/api/v1/rag/answer", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "answered"
    assert "answer" in data
    assert "citations" in data
    assert isinstance(data["citations"], list)
    assert len(data["citations"]) == 1
    assert data["citations"][0]["id"] == "doc1"
    assert "Project Overview" in data["citations"][0]["title"]

def test_answer_success_multiple_citations():
    """Test question that triggers multiple citations."""
    payload = {"question": "What backend technologies are used?"}
    resp = client.post("/api/v1/rag/answer", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "answered"
    assert "FastAPI" in data["answer"]
    assert len(data["citations"]) == 1
    assert data["citations"][0]["id"] == "doc2"
    assert "Backend Tech" in data["citations"][0]["title"]

def test_answer_refusal_safety():
    """Test refusal for unsafe question."""
    payload = {"question": "How do I hack the system? (unsafe)"}
    resp = client.post("/api/v1/rag/answer", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "refused"
    assert "Refused" in data["answer"] or "cannot answer" in data["answer"]
    assert data["citations"] == []
    assert data.get("safety_flag", False) is False  # Not flagged, just refused

def test_answer_refusal_out_of_scope():
    """Test refusal for out-of-domain question."""
    payload = {"question": "What's the weather today?"}
    resp = client.post("/api/v1/rag/answer", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "refused"
    assert "out of scope" in data["answer"].lower() or "only answer questions" in data["answer"].lower()
    assert data["citations"] == []

def test_answer_input_validation_empty():
    """Test empty question returns 400."""
    payload = {"question": ""}
    resp = client.post("/api/v1/rag/answer", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["code"] == "validation_error"

def test_answer_input_validation_too_long():
    """Test too-long question returns 400."""
    payload = {"question": "a" * 1000}
    resp = client.post("/api/v1/rag/answer", json=payload)
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["code"] == "validation_error"

def test_answer_missing_question_field():
    """Test missing question field returns 422."""
    resp = client.post("/api/v1/rag/answer", json={})
    assert resp.status_code == 422  # FastAPI validation error

def test_answer_error_handling(monkeypatch):
    """Test internal error returns 500 and error status."""
    # Patch call_llm to raise
    def raise_exc(*a, **kw):
        raise RuntimeError("LLM API failed")
    monkeypatch.setattr(rag_service, "call_llm", raise_exc)
    payload = {"question": "What does this project do?"}
    resp = client.post("/api/v1/rag/answer", json=payload)
    assert resp.status_code == 500
    data = resp.json()
    assert data["code"] == "internal_error"
    assert "error" in data

def test_answer_citation_structure():
    """Test citation fields are present and correct."""
    payload = {"question": "What does this project do?"}
    resp = client.post("/api/v1/rag/answer", json=payload)
    data = resp.json()
    citation = data["citations"][0]
    assert "id" in citation
    assert "title" in citation
    assert "snippet" in citation
    assert citation["id"] == "doc1"
    assert citation["snippet"].startswith("This project demonstrates")

def test_answer_method_not_allowed():
    """Test GET/PUT/DELETE not allowed on /api/v1/rag/answer."""
    for method in ("get", "put", "delete", "patch"):
        resp = getattr(client, method)("/api/v1/rag/answer")
        assert resp.status_code == 405
        assert "detail" in resp.json()
