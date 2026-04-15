from openai.types.chat import ChatCompletion
import os

from openai import AsyncOpenAI
from loguru import logger

from src.prompts import SUMMARIZE_CONVERSATION_PROMPT


async def summarize_conversation(messages: list) -> str | None:
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response: ChatCompletion = await client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1"),
        messages=[
            {"role": "system", "content": SUMMARIZE_CONVERSATION_PROMPT},
            *messages,
        ],
    )
    return response.choices[0].message.content
