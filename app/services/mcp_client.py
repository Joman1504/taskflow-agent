# app/services/mcp_client.py
# MCP client for the Whisper transcription server.
# Connects over SSE, base64-encodes the audio payload, calls the
# transcribe_audio tool, and returns the resulting transcript text.

import base64

from fastapi import HTTPException
from mcp import ClientSession
from mcp.client.sse import sse_client

# ── Config ────────────────────────────────────────────────────────────────────

MCP_WHISPER_URL = "http://localhost:8001/sse"


# ── Public interface ──────────────────────────────────────────────────────────

async def transcribe_via_mcp(file_bytes: bytes, filename: str) -> str:
    """
    Base64-encode *file_bytes*, open an SSE session with the Whisper MCP
    server, invoke the transcribe_audio tool, and return the transcript.

    Raises:
        HTTPException 503 — if the MCP server is not reachable.
        HTTPException 500 — if the server returns an empty response.
    """
    audio_b64 = base64.b64encode(file_bytes).decode("utf-8")

    try:
        async with sse_client(url=MCP_WHISPER_URL) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "transcribe_audio",
                    {"audio_b64": audio_b64, "filename": filename},
                )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Whisper MCP server is unreachable at {MCP_WHISPER_URL}. "
                f"Start it first with: python mcp_servers/whisper/server.py "
                f"({exc})"
            ),
        ) from exc

    if not result.content:
        raise HTTPException(
            status_code=500,
            detail="Whisper MCP server returned an empty response.",
        )

    return result.content[0].text
