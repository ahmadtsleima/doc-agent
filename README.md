# Document Intelligence Agent

An AI-powered backend that answers questions about your PDF documents using Retrieval-Augmented Generation (RAG). Upload a document, ask a question in natural language, and get an answer grounded **only** in that document's content — with an honest "I couldn't find that in the document" when the answer isn't there.

That refusal is the point. A system that leaks its training knowledge (confidently telling you the capital of France when your document never mentioned it) is a liability. This one knows the boundary of what it was given.

---

## What it does

- **Upload** a PDF through a REST API. It's stored, chunked, embedded, and indexed automatically in one request.
- **Ask** a question. The system finds the most relevant passages by *meaning* (not keywords) and generates an answer grounded in them.
- **Refuses** honestly when the answer isn't in the document, instead of hallucinating.

This is the architecture behind real commercial tools — legal-document search, medical literature Q&A, enterprise knowledge bases.

---

## Architecture

The system has two phases: **ingestion** (once per document, at upload) and **query** (per question).

```
INGESTION                                    QUERY
─────────                                    ─────
PDF upload                                   Question
   │                                            │
   ▼                                            ▼
Extract text (pypdf)                         Embed question
   │                                         (same model, same space)
   ▼                                            │
Chunk (~500 chars, ~100 overlap)                ▼
   │                                         Cosine-distance search
   ▼                                         in pgvector (top-k nearest)
Embed each chunk (3072-dim)                     │
   │                                            ▼
   ▼                                         Ground the LLM in the
Store vectors in pgvector  ◄─────────────────  retrieved chunks
                                                │
                                                ▼
                                             Answer, or honest refusal
```

**Ingestion:** `PDF → extract → chunk with overlap → embed → store in Postgres/pgvector`

**Query:** `question → embed → retrieve nearest chunks → ground the model → answer or refuse`

---

## Key design decisions

The interesting engineering isn't wiring the API — it's these choices:

**Async throughout.** Every LLM and embedding call spends its time *waiting on the network*, not computing. Async releases the worker during that wait, so one worker serves many concurrent requests instead of freezing per call. The rule applied everywhere: `await` anything that leaves the process — network, database, files, AI.

**pgvector inside Postgres, not a separate vector database.** The relational data already lives in Postgres; pgvector adds vector similarity search to the same database. One system to run, no sync between stores. Appropriate for this scale — a dedicated vector store would be a later decision at much larger volume.

**Chunking with overlap.** Chunks too small lose context; too large blur many topics into one averaged vector. ~500-character chunks with ~100-character overlap keep passages precise while ensuring a sentence on a boundary survives intact in at least one chunk. These are tunable starting points, not magic numbers.

**Grounded refusal.** The prompt instructs the model to answer *only* from retrieved context and to say "I couldn't find that in the document" when it can't. Giving the model a legal way to say "I don't know" is what prevents hallucination — forcing an answer is what causes it.

**UUID filenames on disk.** Uploaded files are stored under a generated UUID, never the user's filename. This prevents both silent overwrites (two users uploading `report.pdf`) and path-traversal attacks (a filename like `../main.py` overwriting source code). The original filename is kept only for display.

**Low temperature (0.1) for document Q&A.** Factual answers should be faithful and deterministic-leaning, not creative. Temperature stays near zero.

---

## Tech stack

- **FastAPI** — async Python web framework
- **PostgreSQL + pgvector** — relational storage and 3072-dimensional vector similarity search
- **SQLAlchemy (async)** — ORM with `asyncpg` driver
- **Google Gemini** — LLM (generation) and embedding model
- **Docker Compose** — containerized Postgres
- **pypdf** — PDF text extraction

---

## Running it locally

**Prerequisites:** Python 3.11+, Docker Desktop, a Google Gemini API key.

**1. Clone and enter the project**
```bash
git clone https://github.com/ahmadtsleima/doc-agent.git
cd doc-agent
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS / Linux:
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install "fastapi[standard]" sqlalchemy asyncpg pgvector google-genai python-dotenv pypdf numpy
```

**4. Configure environment**

Copy `.env.example` to `.env` and fill in your values:
```
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3-flash-preview
DATABASE_URL=postgresql+asyncpg://myuser:mypassword@localhost:5433/docagent
```

**5. Start the database**
```bash
docker compose up -d
```

**6. Enable the pgvector extension and create tables**
```bash
# one-time: enable the extension inside the database
docker exec -it doc-agent-db-1 psql -U myuser -d docagent -c "CREATE EXTENSION IF NOT EXISTS vector;"
# create tables
python create_table.py
```

**7. Run the API**
```bash
fastapi dev main.py
```

Open **http://127.0.0.1:8000/docs** for the interactive API documentation.

---

## API endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/upload` | Upload a PDF; it's stored, chunked, embedded, and indexed automatically |
| `POST` | `/ask-document` | Ask a question answered **only** from uploaded documents |
| `POST` | `/ask` | Ask the LLM directly (no document grounding) |
| `POST` | `/ask-stream` | Same as `/ask`, but streams the response token by token |
| `GET` | `/documents` | List uploaded documents |
| `GET` | `/health` | Health check |

---

## What I'd improve next

Being explicit about the limitations, because knowing where a system breaks is part of owning it:

- **Smarter chunking** — currently splits on raw character count, which can cut mid-word. Splitting on sentence or paragraph boundaries would improve retrieval quality. The right approach is to measure both against an evaluation set, not assume.
- **An evaluation suite** — a test set with automated scoring of retrieval accuracy, answer grounding, and correct-refusal rate. This is how you *prove* quality rather than claim it.
- **Vector indexing** — at larger document volumes, an HNSW or IVFFlat index in pgvector would keep search fast.
- **Hybrid search and re-ranking** — combining semantic search with keyword matching, then re-ranking results, typically improves relevance.
- **Background ingestion** — embedding runs serially at upload; for large documents this should move to a background worker (e.g. Celery).
- **Deployment** — currently runs locally; next step is a live deployment with cost and latency monitoring.

---

## About this project

Built from scratch to understand every layer of a production RAG system — not just calling an API, but the engineering underneath it: async request handling, vector storage, retrieval, grounding, and the failure modes (hallucination, injection, data loss) that a careless implementation would hit. Every design decision above is one I can explain and defend.
