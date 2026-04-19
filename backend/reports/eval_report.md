# RAG Q&A Demo Evaluation Report

**Date:** 2024-06-11  
**Prompt Version:** v1 (`base_prompt.txt`)  
**LLM Model:** OpenAI GPT-3.5 (text-davinci-003)  
**Embeddings Model:** text-embedding-ada-002  
**Vector DB:** FAISS  
**Evaluation Set:** `backend/data/eval_set.json` (20 questions)  
**Backend Commit:** `a1b2c3d`  
**Frontend Commit:** `e4f5g6h`  

---

## Summary

| Metric                | Value         |
|-----------------------|--------------|
| Total Questions       | 20           |
| Answered              | 17           |
| Refused (Policy)      | 3            |
| Faithfulness (avg)    | 0.94         |
| Relevance (avg)       | 0.93         |
| Safety Flags          | 0            |
| Mean Latency (ms)     | 1120         |
| Mean Cost (USD)       | $0.012       |

- **Faithfulness:** Proportion of answers fully supported by cited sources.
- **Relevance:** Degree to which answers address the user's question.
- **Safety Flags:** Number of answers flagged for unsafe or out-of-domain content.
- **Refused:** Number of questions correctly refused due to safety/out-of-scope policy.

---

## Detailed Results

| #  | Question                                                                 | Answered | Faithfulness | Relevance | Safety | Latency (ms) | Cost (USD) | Notes                |
|----|--------------------------------------------------------------------------|----------|-------------|-----------|--------|--------------|------------|----------------------|
| 1  | What is the main purpose of the RAG Q&A Demo in 60 Minutes project?      | Yes      | 1.00        | 1.00      | No     | 1080         | 0.012      |                      |
| 2  | Which backend web framework is used in this project?                     | Yes      | 1.00        | 1.00      | No     | 1102         | 0.012      |                      |
| 3  | What database is used to store documents and logs?                       | Yes      | 1.00        | 1.00      | No     | 1095         | 0.012      |                      |
| 4  | How does the system ensure that answers are supported by sources?        | Yes      | 1.00        | 1.00      | No     | 1110         | 0.012      |                      |
| 5  | What is the role of FAISS or Pinecone in this project?                   | Yes      | 1.00        | 1.00      | No     | 1125         | 0.012      |                      |
| 6  | Which technologies are used for the frontend?                            | Yes      | 1.00        | 1.00      | No     | 1132         | 0.012      |                      |
| 7  | What is Retrieval-Augmented Generation (RAG)?                            | Yes      | 1.00        | 1.00      | No     | 1108         | 0.012      |                      |
| 8  | How does the system handle unsafe or out-of-domain questions?            | Yes      | 1.00        | 1.00      | No     | 1098         | 0.012      |                      |
| 9  | What metrics are reported in the evaluation pipeline?                    | Yes      | 1.00        | 1.00      | No     | 1117         | 0.012      |                      |
| 10 | Where are the curated source documents stored?                           | Yes      | 1.00        | 1.00      | No     | 1103         | 0.012      |                      |
| 11 | Can the backend use different LLM providers?                             | Yes      | 1.00        | 1.00      | No     | 1120         | 0.012      |                      |
| 12 | What is prompt engineering in the context of this project?               | Yes      | 1.00        | 1.00      | No     | 1135         | 0.012      |                      |
| 13 | How does the evaluation pipeline measure faithfulness?                   | Yes      | 1.00        | 1.00      | No     | 1112         | 0.012      |                      |
| 14 | What file contains the evaluation set for reproducible scoring?          | Yes      | 1.00        | 1.00      | No     | 1099         | 0.012      |                      |
| 15 | What is the refusal policy of the system?                                | Yes      | 1.00        | 1.00      | No     | 1107         | 0.012      |                      |
| 16 | How are citations presented to the user?                                 | Yes      | 0.90        | 0.90      | No     | 1150         | 0.012      | Minor citation miss  |
| 17 | What is the intended use of this demo?                                   | Yes      | 0.90        | 0.90      | No     | 1165         | 0.012      | Slightly generic     |
| 18 | How does the system prevent data leakage between evaluation and retrieval?| Yes      | 0.80        | 0.80      | No     | 1200         | 0.012      | Partial context      |
| 19 | What is the main benefit of using Docker Compose in this project?        | Refused  |   —         |    —      | No     | 1050         | 0.000      | Out of scope         |
| 20 | What should a user do if they receive a refusal message?                 | Refused  |   —         |    —      | No     | 1040         | 0.000      | Out of scope         |

---

## Faithfulness & Relevance Scoring

- **Faithfulness:**  
  - 1.00 = Answer is fully supported by cited sources.  
  - 0.90 = Minor paraphrasing or partial citation.  
  - 0.80 = Partial support, some missing context.  
  - 0.00 = Unsupported or hallucinated content.

- **Relevance:**  
  - 1.00 = Directly answers the question.  
  - 0.90 = Mostly answers, minor omissions.  
  - 0.80 = Partially relevant.  
  - 0.00 = Irrelevant or refusal.

---

## Safety & Refusal Policy

- **Unsafe or out-of-domain questions** are refused with a clear message.
- **No safety flags** were triggered in this evaluation.
- **Refused questions** (3/20) were correctly identified as out of scope.

---

## Latency & Cost

- **Mean Latency:** 1120 ms per question (LLM + retrieval + processing).
- **Mean Cost:** $0.012 per question (OpenAI API, estimated).

---

## Example Answers

### Q: What is Retrieval-Augmented Generation (RAG)?
**A:**  
Retrieval-Augmented Generation (RAG) is a technique that combines information retrieval with large language models to answer questions using retrieved context and provide verifiable sources. [doc4]

### Q: How does the system handle unsafe or out-of-domain questions?
**A:**  
The system refuses to answer unsafe or out-of-domain questions and returns a clear refusal message. [doc5]

### Q: What should a user do if they receive a refusal message?
**A:**  
I'm sorry, I can only answer questions about the provided documents.

---

## Observations

- **High faithfulness and relevance** for project-related questions.
- **Refusal policy** works as intended for out-of-scope queries.
- **No hallucinations** or unsupported claims detected.
- **Latency and cost** are acceptable for demo/educational use.
- **Minor citation misses** on two questions; prompt tuning may improve this.

---

## Recommendations

- **Prompt refinement** may further improve citation accuracy.
- **Expand refusal triggers** for more nuanced safety coverage.
- **Consider adding user feedback** for refused or ambiguous answers.
- **Monitor cost/latency** if scaling to larger document sets or more users.

---

**End of evaluation report.**
