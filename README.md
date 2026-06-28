# RAG Evaluation & Observability Pipeline

A live LLM observability system that automatically scores RAG outputs across 
multiple quality dimensions and surfaces trends on a public mission control dashboard.

**Live demo:** https://rag-evaluator.onrender.com

## What it does

Most teams build RAG systems and hope the outputs are good. This pipeline measures 
them systematically — scoring every LLM output for faithfulness, relevance, and 
context precision using a hybrid of LLM-as-judge and deterministic metrics.

## Tech Stack
- **FastAPI** — REST API and dashboard server
- **LangChain** — LLM-as-judge evaluation chains
- **Ollama** — local LLM inference (llama3.2)
- **ROUGE** — deterministic overlap scoring
- **Chart.js** — score trend visualisation

## Metrics

| Metric | Measures | Method |
|--------|----------|--------|
| Faithfulness | Is the answer grounded in retrieved context? | LLM-as-judge |
| Relevance | Does the answer address the question? | LLM-as-judge |
| Context Precision | Were retrieved chunks useful? | LLM-as-judge |
| ROUGE-L | Lexical overlap with context | Deterministic |

## Why hybrid scoring?

LLM-as-judge is scalable but subjective. Deterministic metrics like ROUGE are 
objective but miss semantic similarity. Using both triangulates quality more 
reliably than either approach alone — the same strategy used by teams at Google 
and Anthropic.

## Architecture

```
Question + Answer + Context
          ↓
   [Evaluation Pipeline]
    ↓          ↓          ↓
Faithfulness Relevance Context Precision
    ↓          ↓          ↓
         scores.json
              ↓
      Mission Control Dashboard
      - Per query scores
      - Score trends over time
      - Expandable reasoning
      - Live evaluator
```

## Setup & Installation

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.com) installed and running

### 1. Clone the repository
```bash
git clone https://github.com/dheeraj08/rag-evaluator.git
cd rag-evaluator
```

### 2. Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Pull Ollama model
```bash
ollama pull llama3.2
```

### 4. Start Ollama
```bash
ollama serve
```

### 5. Start the server
```bash
uvicorn main:app --reload
```

### 6. Open the dashboard
```
http://127.0.0.1:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/evaluate` | Score a question/answer/context triple |
| GET | `/scores` | Return all stored scores as JSON |
| GET | `/` | Mission control dashboard |
| GET | `/health` | Health check |

## Example evaluation request

```bash
curl -X POST http://127.0.0.1:8000/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is RAG?",
    "answer": "RAG retrieves documents before generating answers.",
    "context": "Retrieval Augmented Generation fetches relevant documents from a knowledge base before passing them to an LLM."
  }'
```

## Key Design Decisions
- **Offline evaluation** — runs as a separate service, not inline with every query, matching how production teams operate
- **Chain-of-Thought prompting** — judge LLM reasons step by step before scoring to reduce subjectivity
- **Fallback score extraction** — if LLM ignores format instructions, regex scans for any valid 0-1 number
- **500 entry cap** — scores.json capped to prevent unbounded disk growth

## Limitations & Future Improvements
- [ ] Replace scores.json with PostgreSQL for production scale
- [ ] Add per-user sessions and authentication
- [ ] Add BERTScore for semantic similarity scoring
- [ ] Add rate limiting to prevent abuse
- [ ] Add webhook alerts when scores drop below threshold
- [ ] Integrate with LangSmith for distributed tracing