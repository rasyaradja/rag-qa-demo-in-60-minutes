# BLUEPRINT.md

## 1. Project Goals

**RAG Q&A Demo in 60 Minutes** aims to teach beginner engineers how to build, prompt, and evaluate a retrieval-augmented Q&A system using modern LLM APIs and vector search. The project’s core goal is to deliver a trustworthy, demo-ready assistant that can answer questions over a curated document set—citing sources, refusing unsafe queries, and reporting measurable quality. The target users are learners and junior engineers seeking hands-on experience with LLM application engineering, focusing on prompt/context strategies, retrieval, and lightweight evaluation.

---

## 2. Features

### Core (MVP)
1. **User Question Submission & Answer Display**
    - Web UI for users to submit questions and receive answers.
2. **Retrieval-Augmented Generation Pipeline**
    - Backend endpoint that embeds queries, retrieves relevant docs from a vector DB, and queries an LLM with contextual prompts.
3. **Source Citation**
    - Answers include citations referencing the supporting documents.
4. **Reproducible Demo Setup**
    - Docker Compose for local setup; pinned dependencies; clear instructions.
5. **Mini Evaluation Pipeline**
    - Script/API to run a 20-question eval set, scoring faithfulness and relevance; report output.
6. **Safety & Refusal Policy**
    - System refuses unsafe or out-of-scope queries and explains why.
7. **Basic Data Hygiene**
    - Curated, documented sources; clear separation of eval and training data.

### Secondary
8. **Prompt/Context Versioning**
    - Track and switch between prompt templates.
9. **Multiple LLM/Embedding Backends**
    - Support for OpenAI, Anthropic, and Hugging Face Llama models.
10. **Latency & Cost Reporting**
    - Capture and display basic latency and cost metrics in eval report.
11. **Admin-only Evaluation Trigger**
    - Restrict evaluation run/report endpoints.

### Future Enhancements
12. **User Authentication**
    - Optional login to track individual sessions.
13. **Advanced Safety & Red-Teaming**
    - Automated adversarial test cases and bias checks.
14. **Interactive Prompt Tuning UI**
    - Web interface to modify and test prompt templates live.
15. **Production-Ready Deployment**
    - Cloud deploy scripts, monitoring, and scaling.

---

## 3. User Stories

1. **As a learner**, I want to ask questions via a web app and get answers with source citations so that I can verify the assistant’s outputs.
2. **As a product evaluator**, I want to run a set of test questions and view a report on faithfulness and relevance so that I can judge the system’s reliability.
3. **As a stakeholder**, I want the assistant to refuse unsafe or out-of-domain questions so that the demo is safe for public/internal use.
4. **As an engineer**, I want to see which prompt template/version is being used so that I can experiment and compare results.

---

## 4. Implementation Order

1. **Set up Monorepo Structure**  
   _Rationale: Ensures clear separation and scaffolding for frontend and backend development._
2. **Implement Backend API Skeleton (FastAPI)**  
   _Rationale: Establishes endpoints for question answering, evaluation, and health checks._
3. **Embed and Store Documents (FAISS/Pinecone Integration)**  
   _Rationale: Enables fast retrieval of relevant context for RAG pipeline._
4. **Develop Frontend UI (Next.js + Tailwind)**  
   _Rationale: Provides user interface for question submission and answer display._
5. **Integrate LLM API Calls and Prompt Construction**  
   _Rationale: Connects retrieval to answer generation with source citation._
6. **Add Safety & Refusal Policies**  
   _Rationale: Ensures system doesn’t answer unsafe/out-of-scope queries._
7. **Build Evaluation Pipeline and Reporting**  
   _Rationale: Enables reproducible quality assessment and reporting._
8. **Implement Prompt/Context Versioning**  
   _Rationale: Supports experimentation and comparison for learning._
9. **Add Latency/Cost Metrics to Reports**  
   _Rationale: Provides transparency on system efficiency and cost._

---

## 5. Data Models

```
UserQuery
  id            UUID      PK
  question      String
  answer        String
  citations     String[]  (references Document.id)
  created_at    DateTime  default now()
  status        Enum('answered', 'refused', 'error')
  llm_model     String
  prompt_version String

Document
  id            UUID      PK
  title         String
  content       Text
  embedding     Vector    (FAISS/Pinecone)
  source_url    String    optional

EvalSet
  id            UUID      PK
  name          String
  questions     JSON      (list of eval questions + gold answers)
  created_at    DateTime

EvalResult
  id            UUID      PK
  eval_set_id   UUID      FK -> EvalSet.id
  query_id      UUID      FK -> UserQuery.id
  faithfulness  Float     (0-1)
  relevance     Float     (0-1)
  safety_flag   Boolean
  latency_ms    Integer
  cost_usd      Float
  created_at    DateTime

PromptTemplate
  id            UUID      PK
  version       String    unique
  template      Text
  created_at    DateTime
```

**Relationships:**
- `UserQuery` references `Document` via `citations`.
- `EvalResult` links an `EvalSet` and a `UserQuery`.
- `PromptTemplate` is referenced by `UserQuery.prompt_version`.

---

## 6. Business Logic

- **RAG Pipeline (backend/app/services/rag_service.py):**
  1. Receive question input.
  2. Embed question using selected embeddings model.
  3. Retrieve top-N similar documents from vector DB.
  4. Construct prompt using selected template and retrieved context.
  5. Call LLM API (OpenAI/Anthropic/HF) and parse response.
  6. Extract and format citations from answer.
  7. Refuse/flag unsafe or out-of-scope queries (using keyword/intent detection).
  8. Log question, answer, citations, model, and prompt version.

- **Evaluation Workflow (backend/app/services/eval_service.py):**
  1. Load eval set (20 Q&A pairs).
  2. For each question, run through RAG pipeline.
  3. Score each answer for faithfulness (does answer align with sources?) and relevance (does it address the question?).
  4. Flag any safety/bias issues.
  5. Aggregate and write results to `reports/eval_report.md` with latency/cost stats.

- **Prompt Versioning (backend/app/core/prompts.py):**
  - Allow switching prompt templates via version identifier in config or API.

- **Safety/Refusal (backend/app/services/rag_service.py):**
  - Check input for unsafe or out-of-domain topics; return refusal message if triggered.

---

## 7. Error Handling Strategy

- **Validation Errors:**  
  - Input validation (empty question, unsupported characters) returns 400 with clear message.
- **Auth Errors:**  
  - (If enabled) 401/403 for protected endpoints (e.g., evaluation trigger).
- **Not Found:**  
  - 404 for missing resources (e.g., document, eval set).
- **Upstream/API Errors:**  
  - 502/503 for LLM or vector DB failures; return generic error to user and log details server-side.
- **Refusal/Policy Violations:**  
  - 200 with explicit refusal message and status `"refused"`.
- **Unexpected Server Errors:**  
  - 500 with generic message; log stack trace for debugging.

_All error responses follow a consistent JSON structure (e.g., `{ "error": "Message", "code": "error_type" }`)._

---

## 8. Security Considerations

- **Authentication/Authorization:**  
  - (Optional for MVP) Restrict evaluation and admin endpoints; otherwise, open for demo.
- **Secrets Management:**  
  - Store API keys and DB credentials in `.env` files; never commit to version control.
- **Input Validation:**  
  - Sanitize and validate all user inputs; enforce length and format constraints.
- **Rate Limiting:**  
  - (Optional for MVP) Apply basic rate limits to API endpoints to prevent abuse.
- **CORS Policy:**  
  - Restrict allowed origins as needed in production.
- **Data Hygiene:**  
  - Use only curated, safe documents; separate eval/test data from training/context sources.

---

## 9. Testing Strategy

- **Unit Tests (backend/tests/):**
  - Core logic for embedding, retrieval, prompt construction, and refusal/safety checks.
- **Integration Tests:**
  - End-to-end test: submit question, check answer and citations.
  - Evaluation pipeline: run eval set, verify report structure and metrics.
- **Acceptance Criteria:**
  - User can submit a question and receive an answer with at least one citation.
  - Unsafe/out-of-domain queries are refused with clear message.
  - Evaluation report is generated with faithfulness and relevance scores for all eval questions.
  - All setup steps reproducible via Docker Compose and documented in README.
- **Manual QA:**
  - Red-team a sample of questions for safety and refusal policy.
  - Confirm prompt version switching changes answer style/quality.

---

This blueprint ensures each lesson builds towards a concrete, shippable capstone—covering LLM API integration, prompt engineering, retrieval, and evaluation, while reinforcing best practices in spec writing, data hygiene, and reproducibility.