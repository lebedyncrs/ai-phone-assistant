import asyncio
import os
from datetime import date

import httpx
import redis.asyncio as aioredis
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from loguru import logger

from src.services.telegram_service import send_message

load_dotenv(override=True)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")
DEEPGRAM_PROJECT_ID = os.getenv("DEEPGRAM_PROJECT_ID", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")


async def _fetch_deepgram_balance(client: httpx.AsyncClient) -> str:
    if not DEEPGRAM_PROJECT_ID:
        logger.warning("DEEPGRAM_PROJECT_ID not set — skipping Deepgram balance")
        return "🎙 Deepgram: _(project ID not configured)_"
    try:
        resp = await client.get(
            f"https://api.deepgram.com/v1/projects/{DEEPGRAM_PROJECT_ID}/balances",
            headers={"Authorization": f"Token {DEEPGRAM_API_KEY}"},
            timeout=10,
        )
        resp.raise_for_status()
        balances = resp.json().get("balances", [])
        if balances:
            amount = balances[0].get("amount", 0)
            units = balances[0].get("units", "USD")
            return f"🎙 Deepgram balance: ${amount:.2f} {units}"
        return "🎙 Deepgram balance: no balance data"
    except Exception as e:
        logger.error(f"Failed to fetch Deepgram balance: {e}")
        return "🎙 Deepgram balance: _(fetch failed)_"


async def _fetch_elevenlabs_usage(client: httpx.AsyncClient) -> str:
    if not ELEVENLABS_API_KEY:
        return "🔊 ElevenLabs: _(API key not configured)_"
    try:
        resp = await client.get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": ELEVENLABS_API_KEY},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        used = data.get("character_count", 0)
        limit = data.get("character_limit", 0)
        return f"🔊 ElevenLabs: {used:,} / {limit:,} chars used"
    except Exception as e:
        logger.error(f"Failed to fetch ElevenLabs usage: {e}")
        return "🔊 ElevenLabs: _(fetch failed)_"


async def _read_and_reset_openai(redis: aioredis.Redis) -> str:
    try:
        async with redis.pipeline() as pipe:
            pipe.getdel("usage:openai:prompt_tokens")
            pipe.getdel("usage:openai:completion_tokens")
            results = await pipe.execute()
        prompt = int(results[0] or 0)
        completion = int(results[1] or 0)
        return f"🤖 OpenAI: {prompt:,} prompt + {completion:,} completion tokens"
    except Exception as e:
        logger.error(f"Failed to read OpenAI usage from Redis: {e}")
        return "🤖 OpenAI: _(Redis read failed)_"


async def send_daily_report():
    logger.info("Sending daily usage report")
    today = date.today().strftime("%Y-%m-%d")
    redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    async with httpx.AsyncClient() as client:
        deepgram_line, elevenlabs_line, openai_line = await asyncio.gather(
            _fetch_deepgram_balance(client),
            _fetch_elevenlabs_usage(client),
            _read_and_reset_openai(redis),
        )

    await redis.aclose()

    message = (
        f"📊 Daily Report — {today}\n\n"
        f"{deepgram_line}\n"
        f"{elevenlabs_line}\n"
        f"{openai_line}"
    )
    await send_message(message)
    logger.info("Daily report sent")


def start_scheduler():
    scheduler = AsyncIOScheduler(timezone="Europe/Warsaw")
    scheduler.add_job(send_daily_report, "cron", hour=10, minute=0)
    scheduler.start()
    logger.info("Scheduler started — daily report at 10:00 Europe/Warsaw")
    return scheduler


async def main():
    scheduler = start_scheduler()
    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
