import asyncio
import io
import os

from telegram import Bot


async def send_message(text: str) -> None:
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    await bot.send_message(chat_id=os.environ["TELEGRAM_CHAT_ID"], text=text)


async def _wav_to_ogg_opus(wav_bytes: bytes) -> bytes:
    process = await asyncio.create_subprocess_exec(
        "ffmpeg", "-i", "pipe:0", "-c:a", "libopus", "-f", "ogg", "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.DEVNULL,
    )
    stdout, _ = await process.communicate(input=wav_bytes)
    return stdout


async def send_voice(audio_bytes: bytes, caption: str) -> None:
    ogg_bytes = await _wav_to_ogg_opus(audio_bytes)
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    buf = io.BytesIO(ogg_bytes)
    buf.name = "recording.ogg"
    await bot.send_voice(chat_id=os.environ["TELEGRAM_CHAT_ID"], voice=buf, caption=caption)