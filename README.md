# TaskFlow Agent

**Dual-Stream Semantic Synthesis System**  
Transforms raw meeting and lecture transcripts into narrative notes and structured action items using an LLM pipeline.

---

## Project Structure

```
taskflow_agent/
├── main.py                     # Entry point — runs uvicorn
├── requirements.txt
├── .env.example                # Copy to .env and fill in your keys
├── .gitignore
├── chroma_store/               # Persistent ChromaDB vector store (auto-created)
├── app/
│   ├── __init__.py             # FastAPI app factory & router registration
│   ├── core/
│   │   └── config.py           # Pydantic-settings config (reads .env)
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── llm_client.py       # Async OpenAI wrapper
│   │   ├── pipeline.py         # Dual-stream pipeline orchestration
│   │   └── rag_service.py      # RAG: chunking, embedding, ChromaDB retrieval
│   └── api/
│       └── routes/
│           └── transcripts.py  # POST /analyze, GET /rag/status
└── frontend/
    └── index.html              # GUI for the agent
```

---

## Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# 4. Run the server
python main.py
# Open http://localhost:8000 OR
# API docs available at http://localhost:8000/docs
```

---

## API

### `POST /api/v1/transcripts/analyze`

**Request body:**
```json
{
  "transcript": "Alice: I'll send the report by Friday. Bob: Let's schedule a review next Monday..."
}
```

**Response:**
```json
{
  "narrative_notes": "The team discussed the upcoming report deadline...",
  "action_items": [
    { "who": "Alice", "what": "Send the report", "when": "Friday" },
    { "who": "Bob", "what": "Schedule a review", "when": "next Monday" }
  ]
}
```

### `GET /health`
Returns `{ "status": "ok" }`.

---

## Dual-Stream Pipeline

| Stream | Output | LLM Role |
|--------|--------|----------|
| Stream 1 | Narrative notes | Summarise themes & decisions in prose |
| Stream 2 | Tactical checklist | Extract Who / What / When commitments as JSON |

Both streams run **in parallel** via `asyncio.gather` to minimise latency.
