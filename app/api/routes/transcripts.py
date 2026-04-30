# app/api/routes/transcripts.py
# API endpoints for transcript processing.

from fastapi import APIRouter, Form, HTTPException, UploadFile, File

from app.models.schemas import TranscriptRequest, DualStreamResponse, TranscribeResponse
from app.services.pipeline import run_dual_stream_pipeline
from app.services.mcp_client import transcribe_via_mcp
from app.services.agent import resolve_transcript

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

_ALLOWED_AUDIO_EXTENSIONS = {
    "mp3", "mp4", "m4a", "wav", "webm", "ogg", "flac", "mov", "mpeg", "mpga"
}

_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB — Whisper API hard limit

# ── API endpoints ─────────────────────────────────────────────────────────────
# 1. /api/v1/transcripts/analyze — accepts a raw text transcript, returns narrative + action items.
@router.post("/analyze", response_model=DualStreamResponse)
async def analyze_transcript(body: TranscriptRequest) -> DualStreamResponse:
    # Validate that the transcript is not empty or just whitespace
    if not body.transcript.strip():
        raise HTTPException(status_code=422, detail="Transcript must not be empty.")

    # Runs the dual-stream pipeline 
    return await run_dual_stream_pipeline(transcript=body.transcript)


# 2. /api/v1/transcripts/process — unified entry point; accepts either text or file, uses the agentic 
# routing layer to decide on transcription, then returns narrative + action items.
@router.post("/process", response_model=DualStreamResponse)
async def process(
    transcript: str | None = Form(None),
    file: UploadFile | None = File(None),
) -> DualStreamResponse:
    """
    Unified entry point. Accepts either a plain-text transcript (form field)
    or an audio/video file upload. The LLM decides whether to call the
    transcribe_audio MCP tool before running the dual-stream pipeline.
    """
    if not transcript and not file:
        raise HTTPException(status_code=422, detail="Provide a transcript or upload a file.")

    file_bytes: bytes | None = None
    filename:   str   | None = None

    # If a file is provided, validate it and read its bytes for potential transcription.
    if file:
        # Validate file type extension and size before sending to the agent
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in _ALLOWED_AUDIO_EXTENSIONS:
            raise HTTPException(
                status_code=415,
                detail=f"Unsupported file type '.{ext}'. Accepted: {', '.join(sorted(_ALLOWED_AUDIO_EXTENSIONS))}",
            )
        file_bytes = await file.read()
        if len(file_bytes) > _MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File exceeds the 25 MB Whisper API limit.")
        filename = file.filename

    # Send the input to the agentic routing layer, which decides whether to call the transcribe_audio tool or proceed directly.
    # This will store the resolved transcript in the variable 'resolved', which is either the original text or the transcribed text from the file.
    resolved = await resolve_transcript(
        text=transcript,        # transcript text if provided, else None
        file_bytes=file_bytes,  # raw bytes of the uploaded file if provided, else None
        filename=filename,      # original filename (used for format detection in transcription) if provided, else None
    )

    if not resolved or not resolved.strip():
        raise HTTPException(status_code=422, detail="Could not produce a transcript from the input.")

    # Run the dual-stream pipeline on the resolved transcript (either the original text or the transcribed text from the file).
    return await run_dual_stream_pipeline(resolved)


# 3. /api/v1/transcripts/transcribe — accepts an audio/video file, returns the transcript text (calls 
# the MCP client directly, bypassing the agent).
@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe(file: UploadFile = File(...)) -> TranscribeResponse:
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in _ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '.{ext}'. Accepted: {', '.join(sorted(_ALLOWED_AUDIO_EXTENSIONS))}",
        )

    file_bytes = await file.read()

    if len(file_bytes) > _MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds the 25 MB Whisper API limit.")

    transcript = await transcribe_via_mcp(file_bytes, file.filename or f"audio.{ext}")
    return TranscribeResponse(transcript=transcript)
