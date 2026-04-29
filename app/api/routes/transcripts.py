from fastapi import APIRouter, HTTPException, UploadFile, File

from app.models.schemas import TranscriptRequest, DualStreamResponse, TranscribeResponse
from app.services.pipeline import run_dual_stream_pipeline
from app.services.whisper_service import transcribe_audio

router = APIRouter(prefix="/transcripts", tags=["transcripts"])

_ALLOWED_AUDIO_EXTENSIONS = {
    "mp3", "mp4", "m4a", "wav", "webm", "ogg", "flac", "mov", "mpeg", "mpga"
}

_MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB — Whisper API hard limit


@router.post("/analyze", response_model=DualStreamResponse)
async def analyze_transcript(body: TranscriptRequest) -> DualStreamResponse:
    if not body.transcript.strip():
        raise HTTPException(status_code=422, detail="Transcript must not be empty.")

    return await run_dual_stream_pipeline(transcript=body.transcript)


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

    transcript = await transcribe_audio(file_bytes, file.filename or f"audio.{ext}")
    return TranscribeResponse(transcript=transcript)
