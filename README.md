# TaskFlow Agent

**Dual-Stream Semantic Synthesis System**  
Transforms raw meeting and lecture transcripts into narrative notes and structured action items using an LLM pipeline. Audio input is transcribed via a dedicated Whisper MCP server.

---

## Project Structure

```
taskflow_agent/
├── main.py                          # Entry point — runs the FastAPI app
├── requirements.txt
├── .env.example                     # Copy to .env and fill in your keys
├── .gitignore
├── mcp_servers/
│   └── whisper/
│       └── server.py                # Whisper MCP server (SSE, port 8001)
├── app/
│   ├── __init__.py                  # FastAPI app factory & router registration
│   ├── core/
│   │   └── config.py                # Pydantic-settings config (reads .env)
│   ├── models/
│   │   └── schemas.py               # Pydantic request/response models
│   ├── services/
│   │   ├── llm_client.py            # Async OpenAI wrapper
│   │   ├── pipeline.py              # Dual-stream pipeline orchestration
│   │   └── mcp_client.py            # MCP client — calls Whisper MCP server
│   └── api/
│       └── routes/
│           └── transcripts.py       # POST /analyze, POST /transcribe
├── frontend/
│   └── index.html                   # GUI for the agent
└── transcript examples/             # Sample transcripts for testing
    ├── ex1.txt
    ├── ex2.txt
    └── ex3.txt
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

# 4. Start the Whisper MCP server (terminal 1)
python mcp_servers/whisper/server.py
# Runs on http://localhost:8001

# 5. Start the FastAPI app (terminal 2)
python main.py
# Open http://localhost:8000 OR
# API docs available at http://localhost:8000/docs
```

---

## Architecture

The app runs as two independent processes:

| Process | Command | Port | Role |
|---------|---------|------|------|
| Whisper MCP server | `python mcp_servers/whisper/server.py` | 8001 | Exposes `transcribe_audio` tool over SSE |
| FastAPI app | `python main.py` | 8000 | Serves frontend, handles requests, calls MCP server |

When a `/transcribe` request arrives, the FastAPI app connects to the Whisper MCP server over SSE, sends the audio as a base64-encoded tool call, and receives the transcript text in return.

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

### `POST /api/v1/transcripts/transcribe`

Accepts a multipart audio file (mp3, mp4, m4a, wav, webm, ogg, flac, mov — max 25 MB). Delegates to the Whisper MCP server and returns the transcript text.

**Response:**
```json
{ "transcript": "..." }
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
