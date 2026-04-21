# app/services/llm_client.py
# Contains the LLM
from openai import AsyncOpenAI
from app.core.config import settings

_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    """Return a singleton AsyncOpenAI client."""
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


async def chat_completion(system_prompt: str, user_prompt: str) -> str:
    """
    Send a single-turn chat completion request to OpenAI and return the
    raw text content of the model's response.
    """
    client = get_client()
    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response.choices[0].message.content or ""
