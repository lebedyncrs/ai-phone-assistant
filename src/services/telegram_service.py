import os
from telegram import Bot

async def send_message(text: str) -> None:
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    await bot.send_message(chat_id=os.environ["TELEGRAM_CHAT_ID"], text=text)