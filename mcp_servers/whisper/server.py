# mcp_servers/whisper/server.py
# Standalone MCP server that exposes a single tool — transcribe_audio — over
# SSE transport on localhost:8001. Run this process independently before
# starting the FastAPI app:
#
#   python mcp_servers/whisper/server.py

import base64
import io
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from openai import AsyncOpenAI

# ── Environment ───────────────────────────────────────────────────────────────
# Load .env from the project root (two directories above this file)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

# ── Server definition ─────────────────────────────────────────────────────────
mcp = FastMCP("whisper-transcription")

# ── OpenAI client singleton ───────────────────────────────────────────────────
_openai_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Ensure the project .env file is present and contains the key."
            )
        _openai_client = AsyncOpenAI(api_key=api_key)
    return _openai_client


# ── Tool definition ───────────────────────────────────────────────────────────

@mcp.tool()
async def transcribe_audio(audio_b64: str, filename: str) -> str:
    """
    Transcribe an audio or video file using OpenAI Whisper.

    Args:
        audio_b64: Base64-encoded bytes of the audio/video file.
        filename:  Original filename including extension (e.g. "recording.mp3").
                   The extension is used by the Whisper API for format detection.

    Returns:
        The full transcript as a plain-text string.
    """
    client = _get_client()

    audio_bytes = base64.b64decode(audio_b64)
    audio_file  = io.BytesIO(audio_bytes)
    audio_file.name = filename  # Whisper API uses the name attribute for format detection

    response = await client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
    )
    return response.text


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("Starting Whisper MCP server on http://localhost:8001 ...")
    uvicorn.run(mcp.sse_app(), host="0.0.0.0", port=8001)
