# app/models/schema.py
# This contains all of our Pydantic models
from pydantic import BaseModel, Field


# ── Request ──────────────────────────────────────────────────────────────────

class TranscriptRequest(BaseModel):
    transcript: str  = Field(..., description="Raw meeting or lecture transcript text.")
    use_rag:    bool = Field(False, description="When True, retrieve relevant context from past transcripts and inject it into the LLM prompts.")


# ── Stream 2: Tactical Checklist ─────────────────────────────────────────────

class ActionItem(BaseModel):
    who: str = Field(..., description="Speaker or assignee responsible for the task.")
    what: str = Field(..., description="Description of the task or commitment.")
    when: str | None = Field(None, description="Deadline or urgency indicator, if stated.")


# ── Stream 1 + Stream 2 combined response ────────────────────────────────────

class DualStreamResponse(BaseModel):
    narrative_notes: str = Field(
        ...,
        description="Stream 1 — concise narrative summary of themes and key discussion points.",
    )
    action_items: list[ActionItem] = Field(
        ...,
        description="Stream 2 — structured tactical checklist of Who / What / When commitments.",
    )


# ── RAG status ───────────────────────────────────────────────────────────────

class RAGStatusResponse(BaseModel):
    indexed_chunks: int = Field(..., description="Number of text chunks currently stored in the vector knowledge base.")
    collection:     str = Field(..., description="Name of the ChromaDB collection.")
