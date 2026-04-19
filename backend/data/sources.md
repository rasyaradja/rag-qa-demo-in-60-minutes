# Curated Source Documents for RAG Q&A Demo

This file contains the canonical, safe, and well-documented source documents used for retrieval and context in the RAG Q&A assistant. Each document is clearly delimited and includes a unique ID, title, optional source URL, and content. These documents are embedded and indexed in the vector database for retrieval-augmented generation.

---

## Document: doc1

**Title:** Project Overview  
**Source URL:** https://github.com/example/rag-qa-demo

**Content:**

The "RAG Q&A Demo in 60 Minutes" is a beginner-friendly, full-stack application that demonstrates how to build a Retrieval-Augmented Generation (RAG) Q&A assistant using modern large language model (LLM) APIs and vector search. The project provides a working web demo for querying a curated set of documents, with answers that cite their sources. It also includes a reproducible evaluation pipeline measuring answer faithfulness, relevance, and safety.

---

## Document: doc2

**Title:** Backend Technology Stack  
**Source URL:** https://fastapi.tiangolo.com/

**Content:**

The backend of the RAG Q&A Demo is built with FastAPI, a modern, high-performance web framework for building APIs with Python 3.11+. It uses SQLAlchemy 2.0 (async) for database access and PostgreSQL as the primary data store. Document embeddings are generated using models such as OpenAI's `text-embedding-ada-002`, and stored in a vector database (FAISS or Pinecone) for efficient similarity search. The backend orchestrates retrieval, prompt construction, LLM calls, and evaluation logic.

---

## Document: doc3

**Title:** Frontend Technology Stack  
**Source URL:** https://nextjs.org/

**Content:**

The frontend is implemented using Next.js 14 with the App Router, providing a modern React-based user interface. TypeScript 5 ensures type safety, and Tailwind CSS is used for rapid, consistent styling. The frontend allows users to submit questions, view answers with citations, and interact with the assistant in real time. It communicates with the backend via REST API endpoints.

---

## Document: doc4

**Title:** Retrieval-Augmented Generation (RAG) Pipeline  
**Source URL:** https://www.pinecone.io/learn/retrieval-augmented-generation/

**Content:**

Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with large language models to answer questions more accurately and with verifiable sources. The pipeline works by embedding the user’s question, retrieving the most relevant documents from a vector database, constructing a prompt with the retrieved context, and querying an LLM to generate an answer. The answer includes citations to the supporting documents.

---

## Document: doc5

**Title:** Safety and Refusal Policy  
**Source URL:** https://platform.openai.com/docs/guides/safety-best-practices

**Content:**

The RAG Q&A assistant is designed with safety in mind. It refuses to answer unsafe or out-of-domain questions, such as those involving personal data, illegal activities, or harmful content. When a question is refused, the system returns a clear refusal message and does not generate an answer. Safety checks are performed using keyword and intent detection, and all source documents are curated for appropriateness.

---

## Document: doc6

**Title:** Evaluation Pipeline and Metrics  
**Source URL:** https://arxiv.org/abs/2309.00864

**Content:**

The evaluation pipeline runs a set of curated questions through the RAG system and scores each answer for faithfulness (does the answer align with the retrieved sources?) and relevance (does it address the question?). Safety and refusal cases are also flagged. The results are aggregated into a markdown report, including latency and cost metrics, to provide a transparent assessment of system quality.

---

## Document: doc7

**Title:** Prompt Engineering and Versioning  
**Source URL:** https://www.promptingguide.ai/

**Content:**

Prompt engineering is the practice of designing and refining the instructions given to large language models to optimize their outputs. In this project, prompt templates are versioned and stored separately, allowing experimentation and comparison of different prompt strategies. The backend supports switching between prompt versions for both answering and evaluation.

---

## Document: doc8

**Title:** Data Hygiene and Document Curation  
**Source URL:** https://www.datacurationnetwork.org/

**Content:**

All documents used for retrieval are carefully curated to ensure accuracy, safety, and appropriateness. Evaluation sets are kept separate from the retrieval corpus to avoid data leakage. The project follows best practices in data hygiene, including clear documentation of sources and regular review of content for safety and relevance.

---

## Document: doc9

**Title:** Supported LLM and Embedding Providers  
**Source URL:** https://platform.openai.com/docs/

**Content:**

The RAG Q&A Demo supports multiple LLM and embedding providers, including OpenAI (GPT-3.5/4, Ada), Anthropic (Claude), and Hugging Face (Llama). The backend can be configured to use different models and APIs via environment variables. This flexibility allows users to experiment with various model backends and compare their performance.

---

## Document: doc10

**Title:** System Limitations and Intended Use  
**Source URL:** https://github.com/example/rag-qa-demo#limitations

**Content:**

This demo is intended for educational and prototyping purposes only. It is not production-hardened and should not be used for sensitive or mission-critical applications. The system is limited to answering questions about the curated document set and may refuse or fail to answer questions outside its scope. Users are encouraged to review answers and citations for accuracy.

---

**End of source documents.**
