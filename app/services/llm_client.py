# app/services/llm_client.py
# Wrapper around the OpenAI AsyncOpenAI client.
# Provides a singleton client instance and helper functions for common patterns.
from openai import AsyncOpenAI
from app.core.config import settings

_client: AsyncOpenAI | None = None

# Singleton client factory
def get_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client

# Helper function for sending a single-turn chat completion request with system and user prompts.
async def chat_completion(system_prompt: str, user_prompt: str) -> str:
    """
    Send a single-turn chat completion request to OpenAI and return the
    raw text content of the model's response.
    """
    client = get_client()

    # Send the system and user prompts to OpenAI as a single message list.
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},   # System prompt sets the behavior and instructions for the model.
            {"role": "user", "content": user_prompt},       # User prompt contains the transcript or file description that the model will analyze.
        ],
    )
    return response.choices[0].message.content or ""
