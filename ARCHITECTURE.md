# ARCHITECTURE.md

## 1. Project Overview

**RAG Q&A Demo in 60 Minutes** is a beginner-friendly, full-stack application that demonstrates how to build a Retrieval-Augmented Generation (RAG) Q&A assistant using modern LLM APIs and vector search. The primary users are learners and junior engineers aiming to understand LLM application engineering, prompt/context strategies, and evaluation methods. The project provides a working web demo for querying a small document set, plus a reproducible evaluation pipeline measuring answer faithfulness, relevance, and safety.

---

## 2. Tech Stack

- **Next.js 14 (App Router)**  
  For a modern, performant React-based web frontend with rapid prototyping and SSR/SSG capabilities.
- **TypeScript 5**  
  Ensures type safety and maintainable code in the frontend.
- **Tailwind CSS**  
  Enables fast, consistent, and responsive UI styling.
- **FastAPI**  
  Provides a high-performance, Pythonic backend for API endpoints and orchestration logic.
- **Python 3.11+**  
  Modern Python runtime for backend logic, LLM orchestration, and evaluation scripts.
- **SQLAlchemy 2.0 (async)**  
  Manages database models and async DB access for tracking queries and evaluation results.
- **PostgreSQL**  
  Reliable open-source relational database for storing documents and logs.
- **FAISS (or Pinecone)**  
  Vector database for fast similarity search over document embeddings.
- **LangChain or LlamaIndex**  
  Orchestration frameworks to connect LLMs, embedding models, and vector search.
- **OpenAI/Anthropic/Hugging Face Llama**  
  Provides LLM APIs for answering user queries.
- **Docker Compose**  
  Simplifies local setup and ensures reproducibility across environments.
- **Pytest**  
  For backend and evaluation pipeline testing.
- **Markdown/JSON**  
  For storing curated sources, prompt templates, and evaluation sets.

---

## 3. Directory Structure

```
my-project/
├── frontend/                   # Next.js application
│   ├── app/
│   │   ├── page.tsx
│   │   ├── layout.tsx
│   │   └── api/                # (optional for frontend proxying)
│   ├── components/
│   │   ├── QueryForm.tsx
│   │   ├── AnswerDisplay.tsx
│   │   └── CitationList.tsx
│   ├── lib/
│   │   └── api.ts              # API client for backend calls
│   ├── public/
│   ├── .env.local
│   ├── next.config.ts
│   ├── package.json
│   └── tsconfig.json
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── rag.py
│   │   │   │   ├── eval.py
│   │   │   │   └── health.py
│   │   │   └── __init__.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── llm.py
│   │   │   ├── embeddings.py
│   │   │   ├── vectorstore.py
│   │   │   └── prompts.py
│   │   ├── models/
│   │   │   ├── document.py
│   │   │   ├── query.py
│   │   │   └── eval.py
│   │   ├── schemas/
│   │   │   ├── rag.py
│   │   │   ├── eval.py
│   │   │   └── base.py
│   │   ├── services/
│   │   │   ├── rag_service.py
│   │   │   ├── eval_service.py
│   │   │   └── data_prep.py
│   │   └── main.py
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   ├── tests/
│   │   ├── test_rag.py
│   │   ├── test_eval.py
│   │   └── test_health.py
│   ├── data/
│   │   ├── sources.md          # Curated source docs
│   │   ├── eval_set.json       # 20-question eval set
│   │   └── prompts/
│   │       └── base_prompt.txt
│   ├── reports/
│   │   └── eval_report.md      # Generated evaluation report
│   ├── .env
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env                        # Shared env vars (DB URL, secrets)
├── README.md
└── ARCHITECTURE.md
```

---

## 4. Key Components

### Frontend (`frontend/`)
- **App & Components:** Implements the user interface for querying the assistant, displaying answers, and showing citations. Handles user input and communicates with the backend API.
- **Lib:** Contains API client utilities for interacting with backend endpoints.

### Backend (`backend/`)
- **API Endpoints:** Exposes REST endpoints for question answering (`rag.py`), evaluation (`eval.py`), and health checks.
- **Core:** Manages configuration, LLM API integration, embeddings generation, vector store setup (FAISS/Pinecone), and prompt templates.
- **Models & Schemas:** Define database models (documents, queries, eval results) and Pydantic schemas for API I/O.
- **Services:** Orchestrate retrieval, prompt construction, LLM calls, evaluation scoring, and data prep routines.
- **Data:** Stores curated source documents, prompt templates, and evaluation datasets for reproducible experiments.
- **Reports:** Contains generated evaluation reports for quality, safety, and latency/cost assessment.

### Infrastructure
- **Docker Compose:** Orchestrates frontend, backend, and database containers for local development.
- **Alembic:** Handles database migrations.
- **Tests:** Provides automated tests for backend endpoints and evaluation logic.

---

## 5. Data Flow

```
1. User submits a question via the frontend UI.
2. Frontend sends a POST request to `/api/v1/rag/answer` on the backend.
3. Backend:
   a. Embeds the user question.
   b. Searches vector DB (FAISS/Pinecone) for relevant documents.
   c. Constructs a prompt with context and sends it to the LLM API.
   d. Receives the LLM's answer and extracts citations.
   e. Returns answer and citations to the frontend.
4. Frontend displays the answer and source citations to the user.
5. For evaluation, backend runs the eval set through the same pipeline, scoring faithfulness and relevance, and writes results to `reports/eval_report.md`.
```

---

## 6. API Design

| Method | Path                    | Description                                      |
|--------|-------------------------|--------------------------------------------------|
| POST   | `/api/v1/rag/answer`    | Submit a user question; receive answer + sources |
| GET    | `/api/v1/rag/health`    | Health check endpoint                            |
| POST   | `/api/v1/eval/run`      | Run evaluation set and generate a report         |
| GET    | `/api/v1/eval/report`   | Fetch the latest evaluation report               |

---

## 7. Environment Variables

| Variable                 | Default                | Required | Description                                             |
|--------------------------|------------------------|----------|---------------------------------------------------------|
| `OPENAI_API_KEY`         | (none)                 | Yes      | API key for OpenAI LLM access                           |
| `ANTHROPIC_API_KEY`      | (none)                 | No       | API key for Anthropic (optional alternative)            |
| `HF_TOKEN`               | (none)                 | No       | Hugging Face token for Llama models (if used)           |
| `VECTOR_DB`              | `faiss`                | No       | Vector DB backend: `faiss` or `pinecone`                |
| `PINECONE_API_KEY`       | (none)                 | No       | Pinecone API key (if using Pinecone)                    |
| `DATABASE_URL`           | `postgresql://...`     | Yes      | PostgreSQL connection URL                               |
| `EMBEDDINGS_MODEL`       | `text-embedding-ada-002`| No      | Embeddings model to use                                 |
| `ALLOWED_ORIGINS`        | `*`                    | No       | CORS allowed origins for API                            |
| `PROMPT_VERSION`         | `v1`                   | No       | Prompt template version                                 |
| `EVAL_SET_PATH`          | `data/eval_set.json`   | No       | Path to evaluation set file                             |
| `SECRET_KEY`             | (none)                 | Yes      | Secret key for backend session/security                 |
| `PORT`                   | `8000`                 | No       | Backend server port                                     |

---

This architecture enables rapid prototyping, reproducible evaluation, and clear separation of concerns—supporting lesson-by-lesson learning and robust, industry-aligned engineering practices.