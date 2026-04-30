# app/services/pipeline.py
# Core logic for the dual-stream processing pipeline.
# Contains the system prompts and the main function that runs both the narrative and tactical streams in parallel.

import asyncio
import json

from app.services.llm_client import chat_completion
from app.models.schemas import ActionItem, DualStreamResponse

_NARRATIVE_SYSTEM = """
You are an expert meeting analyst. Given a raw transcript, produce a concise
narrative summary (1-3 short paragraphs) that captures the core themes, key
decisions, and important discussion points. Write in clear, professional prose.
Do not include action items — focus solely on summarising what was discussed.
""".strip()

_TACTICAL_SYSTEM = """
You are an expert at extracting commitments from transcripts. Given a raw transcript,
identify every firm action item where someone explicitly commits to doing something
or is assigned to do something. Ignore suggestions, hypotheticals, and vague statements
like "we should".

Return ONLY a valid JSON array with this exact structure; no extra text:
[
    {"who": "<person or role>", "what": "<task description>", "when": "<deadline or null>"},
    ...
]

Rules:
- "who" must be the speaker or the assignee, not a team or organisation name.
- "when" is null if no deadline or timeframe was mentioned.
- Only include items with a clear commitment verb (will, going to, I'll, need to, you have to, etc.).
""".strip()


async def run_dual_stream_pipeline(transcript: str) -> DualStreamResponse:
    """
    Run Stream 1 (narrative notes) and Stream 2 (tactical checklist) in
    parallel against the same transcript, then combine into a DualStreamResponse.
    """
    # Asynchronously run both the narrative and tactical streams using asyncio.gather.
    # Utilizes the chat_completion helper to send the respective system prompts and the transcript as the user prompt.
    narrative_task = asyncio.create_task(chat_completion(_NARRATIVE_SYSTEM, transcript))
    tactical_task  = asyncio.create_task(chat_completion(_TACTICAL_SYSTEM, transcript))

    narrative_text, tactical_text = await asyncio.gather(narrative_task, tactical_task)

    # Parse the tactical stream's JSON output into a list of ActionItem objects.
    try:
        raw_items: list[dict] = json.loads(tactical_text)
        action_items = [ActionItem(**item) for item in raw_items]
    except (json.JSONDecodeError, TypeError, ValueError):
        action_items = []

    return DualStreamResponse(
        narrative_notes=narrative_text.strip(),
        action_items=action_items,
    )
