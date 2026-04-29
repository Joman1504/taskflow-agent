import io
from app.services.llm_client import get_client


async def transcribe_audio(file_bytes: bytes, filename: str) -> str:
    """
    Send audio/video bytes to OpenAI Whisper and return the transcript text.
    filename is used so OpenAI can detect the file format from the extension.
    """
    client = get_client()
    audio_file = io.BytesIO(file_bytes)
    audio_file.name = filename

    response = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    return response.text
