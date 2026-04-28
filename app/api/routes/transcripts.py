# app/api/routes/transcripts.py
# Transcript analysis endpoint and RAG knowledge-base status endpoint.

import asyncio
from fastapi import APIRouter, HTTPException

from app.models.schemas import TranscriptRequest, DualStreamResponse, RAGStatusResponse
from app.services.pipeline import run_dual_stream_pipeline
from app.services.rag_service import index_transcript, get_stats

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/analyze", response_model=DualStreamResponse)
async def analyze_transcript(body: TranscriptRequest) -> DualStreamResponse:
    """
    Accept a raw transcript and return the dual-stream analysis:
    - Stream 1: narrative notes
    - Stream 2: structured action items (Who / What / When)

    When *use_rag* is True the system retrieves relevant context from
    previously indexed transcripts and injects it into the LLM prompts
    before analysis. Regardless of the flag, every successfully analysed
    transcript is automatically indexed into the RAG knowledge base so
    the store grows with each use.
    """
    if not body.transcript.strip():
        raise HTTPException(status_code=422, detail="Transcript must not be empty.")

    result = await run_dual_stream_pipeline(
        transcript=body.transcript,
        use_rag=body.use_rag,
    )

    # Auto-index in the background — fire-and-forget so it doesn't delay the response
    asyncio.create_task(index_transcript(body.transcript))

    return result


@router.get("/rag/status", response_model=RAGStatusResponse, tags=["rag"])
async def rag_status() -> RAGStatusResponse:
    """Return the current state of the RAG knowledge base."""
    stats = get_stats()
    return RAGStatusResponse(**stats)
