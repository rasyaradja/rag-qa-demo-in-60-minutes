# RAG Q&A Demo in 60 Minutes

A beginner-friendly, full-stack Retrieval-Augmented Generation (RAG) Q&A assistant demo. Ask questions about a curated set of project documents and get answers with source citations—powered by modern LLM APIs, vector search, and reproducible evaluation.

---

## 🚀 Features

- **Web UI**: Ask questions, view answers, and see supporting citations.
- **Retrieval-Augmented Generation**: Combines vector search (FAISS/Pinecone) with LLMs (OpenAI/Anthropic/Hugging Face).
- **Source Citation**: Answers include references to supporting documents.
- **Safety & Refusal Policy**: Refuses unsafe or out-of-scope queries.
- **Reproducible Evaluation**: Run a 20-question eval set, scoring faithfulness, relevance, and safety.
- **Prompt Versioning**: Experiment with different prompt templates.
- **Docker Compose**: One-command local setup.

---

## 🏗️ Tech Stack

- **Frontend**: Next.js 14 (App Router), TypeScript 5, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+, SQLAlchemy 2.0 (async)
- **Database**: PostgreSQL
- **Vector DB**: FAISS (default) or Pinecone
- **LLM APIs**: OpenAI, Anthropic, Hugging Face Llama
- **Orchestration**: LangChain or LlamaIndex
- **Containerization**: Docker Compose

---

## 📂 Project Structure

```
my-project/
├── frontend/         # Next.js app (UI, components, API client)
├── backend/          # FastAPI app (API, RAG logic, eval, data)
├── docker-compose.yml
├── .env              # Shared env vars (DB, API keys)
├── README.md
└── ARCHITECTURE.md
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for a detailed breakdown.

---

## ⚡ Quickstart

### 1. Clone the Repo

```bash
git clone https://github.com/example/rag-qa-demo.git
cd rag-qa-demo
```

### 2. Set Up Environment Variables

Copy and edit the `.env` files:

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

**Required keys:**

- `OPENAI_API_KEY` (for OpenAI LLM/embeddings)
- `DATABASE_URL` (PostgreSQL connection string)
- `SECRET_KEY` (backend session/security)

See [Environment Variables](#-environment-variables) for all options.

### 3. Build and Start All Services

```bash
docker-compose up --build
```

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)

### 4. Try the Demo

- Open the web UI and ask a question about the project (e.g., "What is Retrieval-Augmented Generation?").
- Answers will include citations to supporting documents.

---

## 📝 Usage

### Ask a Question

1. Enter your question in the web UI.
2. Submit and view the answer, with a list of cited sources.

### Example Questions

- "What backend framework does this project use?"
- "How does the system ensure answer faithfulness?"
- "What is the refusal policy?"

### Run Evaluation Pipeline

To generate an evaluation report (admin only, by default):

```bash
# From backend container or host with env vars set
curl -X POST http://localhost:8000/api/v1/eval/run
```

- Results are saved to `backend/reports/eval_report.md`.
- View via API: `GET /api/v1/eval/report`

---

## 🛠️ Development

### Frontend

```bash
cd frontend
npm install
npm run dev
```

- Edit UI in `components/` and `app/`.
- API client in `lib/api.ts`.

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head  # Run DB migrations
uvicorn app.main:app --reload
```

- API endpoints in `app/api/v1/endpoints/`.
- RAG logic in `app/services/rag_service.py`.
- Evaluation in `app/services/eval_service.py`.

### Database

- Uses PostgreSQL (see `docker-compose.yml` for default config).
- Alembic for migrations.

### Vector DB

- Default: FAISS (local, no API key needed).
- Pinecone: Set `VECTOR_DB=pinecone` and provide `PINECONE_API_KEY`.

---

## 🧪 Testing

### Backend

```bash
cd backend
pytest
```

- Unit and integration tests in `backend/tests/`.

### Frontend

```bash
cd frontend
npm run test
```

---

## ⚙️ Environment Variables

| Variable                 | Required | Description                                      |
|--------------------------|----------|--------------------------------------------------|
| `OPENAI_API_KEY`         | Yes      | OpenAI API key for LLM/embeddings                |
| `ANTHROPIC_API_KEY`      | No       | Anthropic Claude API key (optional)              |
| `HF_TOKEN`               | No       | Hugging Face token for Llama models (optional)   |
| `VECTOR_DB`              | No       | `faiss` (default) or `pinecone`                  |
| `PINECONE_API_KEY`       | No       | Pinecone API key (if using Pinecone)             |
| `DATABASE_URL`           | Yes      | PostgreSQL connection string                     |
| `EMBEDDINGS_MODEL`       | No       | Embeddings model (default: `text-embedding-ada-002`) |
| `ALLOWED_ORIGINS`        | No       | CORS allowed origins (default: `*`)              |
| `PROMPT_VERSION`         | No       | Prompt template version (default: `v1`)          |
| `EVAL_SET_PATH`          | No       | Path to eval set file                            |
| `SECRET_KEY`             | Yes      | Backend session/security key                     |
| `PORT`                   | No       | Backend server port (default: `8000`)            |

See `.env.example` files for templates.

---

## 📊 Evaluation & Reporting

- **Run evaluation:** `POST /api/v1/eval/run`
- **Fetch report:** `GET /api/v1/eval/report`
- **Metrics:** Faithfulness, relevance, safety, latency, cost
- **Report file:** `backend/reports/eval_report.md`

See [backend/reports/eval_report.md](backend/reports/eval_report.md) for a sample.

---

## 🔒 Safety & Refusal Policy

- Unsafe or out-of-scope questions are refused with a clear message.
- Only answers questions about the curated project documents.
- All source docs are reviewed for safety and appropriateness.

---

## 🧹 Data Hygiene

- Source documents: [`backend/data/sources.md`](backend/data/sources.md)
- Evaluation set: [`backend/data/eval_set.json`](backend/data/eval_set.json)
- Prompt templates: [`backend/data/prompts/`](backend/data/prompts/)

---

## 📝 API Reference

| Method | Path                    | Description                                      |
|--------|-------------------------|--------------------------------------------------|
| POST   | `/api/v1/rag/answer`    | Submit a user question; receive answer + sources |
| GET    | `/api/v1/rag/health`    | Health check endpoint                            |
| POST   | `/api/v1/eval/run`      | Run evaluation set and generate a report         |
| GET    | `/api/v1/eval/report`   | Fetch the latest evaluation report               |

See [backend/app/api/v1/endpoints/](backend/app/api/v1/endpoints/) for details.

---

## 🧩 Prompt Engineering

- Prompt templates are versioned in `backend/data/prompts/`.
- Switch prompt version via `PROMPT_VERSION` env variable.
- Experiment with prompt wording to improve answer quality and citation accuracy.

---

## 🛡️ Security

- API keys and secrets are **never** committed—use `.env` files.
- Input validation and refusal logic prevent unsafe queries.
- (Optional) Restrict evaluation endpoints for admin use.

---

## 📝 License

MIT License.  
For educational and prototyping use only. Not production-hardened.

---

## 🙋 FAQ

**Q:** What questions can I ask?  
**A:** Anything about the project’s curated documents (see "sources.md"). Out-of-scope or unsafe questions will be refused.

**Q:** Can I use my own documents?  
**A:** Yes! Replace or add to `backend/data/sources.md` and re-run the embedding/indexing step.

**Q:** How do I switch LLM or vector DB providers?  
**A:** Set the relevant env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `VECTOR_DB`, etc.) and restart the backend.

**Q:** How do I contribute?  
**A:** Fork, branch, and submit a PR! See [CONTRIBUTING.md](CONTRIBUTING.md) (if present) or open an issue.

---

## 📚 Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and rationale
- [BLUEPRINT.md](BLUEPRINT.md) — Feature plan and business logic
- [backend/data/sources.md](backend/data/sources.md) — Curated source docs
- [backend/data/eval_set.json](backend/data/eval_set.json) — Evaluation set
- [backend/reports/eval_report.md](backend/reports/eval_report.md) — Sample evaluation report

---

**Happy hacking!**  
Questions or feedback? [Open an issue](https://github.com/example/rag-qa-demo/issues) or ping us on GitHub.