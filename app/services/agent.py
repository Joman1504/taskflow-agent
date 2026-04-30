# app/services/agent.py
# Agentic routing layer.
# Makes a single LLM call with the transcribe_audio tool available.
# The LLM inspects the input description and decides whether to call the
# tool (audio/video file) or proceed directly (text transcript).

from app.core.config import settings
from app.services.llm_client import get_client
from app.services.mcp_client import transcribe_via_mcp

# ── System prompt ─────────────────────────────────────────────────────────────

_SYSTEM = """
You are a routing agent. Your only job is to decide whether the user's input
needs audio transcription before it can be processed.

- If the user submitted a text transcript: reply with exactly the word READY.
- If the user uploaded an audio or video file: call the transcribe_audio tool.

Do not explain yourself. Do not produce any other output.
""".strip()

# ── Tool definition (passed to the LLM) ──────────────────────────────────────

_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "transcribe_audio",
            "description": "Transcribe an audio or video file to text using OpenAI Whisper.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }
]

# ── Public interface ──────────────────────────────────────────────────────────

async def resolve_transcript(
    text: str | None = None,            # Raw transcript text if provided by the user, otherwise None
    file_bytes: bytes | None = None,    # Raw bytes of the uploaded audio/video file if provided by the user, otherwise None
    filename: str | None = None,        # Original filename of the uploaded file (used for format detection in transcription) if provided by the user, otherwise None
) -> str:
    """
    Ask the LLM whether transcription is needed.

    - If *text* is provided, the LLM will reply READY and we return the text.
    - If *file_bytes* + *filename* are provided, the LLM will call
    transcribe_audio, which triggers the MCP client and returns the transcript.
    """
    client = get_client()

    # Construct the user message based on whether we received text or a file. 
    # This message is what the LLM will use to determine whether to call the transcription tool or not.
    user_msg = (
        f"The user submitted a text transcript ({len(text):,} characters)."
        if text
        else f"The user uploaded a file named '{filename}'."
    )

    # Send the system and user prompts to OpenAI as a single message list, along with the tool definition. 
    # The LLM will decide whether to call the tool or not based on the content of the user message.
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": user_msg},
        ],
        tools=_TOOLS,
        tool_choice="auto",
    )

    # Check if the LLM decided to call the transcribe_audio tool. If so, delegate to the MCP client to perform transcription.
    if response.choices[0].message.tool_calls:
        # LLM decided this is audio — delegate to the Whisper MCP server
        # Returns the transcribed text from the audio file
        return await transcribe_via_mcp(file_bytes, filename)

    # LLM decided it is already a transcript
    return text
