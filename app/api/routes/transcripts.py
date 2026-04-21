# app/api/routes/transcripts.py
# Contains the POST endpoint for transcript analysis. 

from fastapi import APIRouter, HTTPException
from app.models.schemas import TranscriptRequest, DualStreamResponse
from app.services.pipeline import run_dual_stream_pipeline

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


@router.post("/analyze", response_model=DualStreamResponse)
async def analyze_transcript(body: TranscriptRequest) -> DualStreamResponse:
    """
    Accept a raw transcript and return the dual-stream analysis:
    - Stream 1: narrative notes
    - Stream 2: structured action items (Who / What / When)
    """
    if not body.transcript.strip():
        raise HTTPException(status_code=422, detail="Transcript must not be empty.")

    return await run_dual_stream_pipeline(body.transcript)
