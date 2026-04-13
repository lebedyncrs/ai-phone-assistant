
import asyncio
import os

from loguru import logger
from twilio.rest import Client

from src.dto.call_info import CallInfo


async def hangup_call(call_sid: str) -> None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        logger.warning("Missing Twilio credentials, cannot hang up call")
        return

    def _hangup():
        client = Client(account_sid, auth_token)
        client.calls(call_sid).update(status="completed")

    try:
        await asyncio.to_thread(_hangup)
        logger.info(f"Hung up Twilio call {call_sid}")
    except Exception as e:
        logger.error(f"Error hanging up Twilio call {call_sid}: {e}")


async def get_call_info(call_sid: str) -> CallInfo | None:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        logger.warning("Missing Twilio credentials, cannot fetch call info")
        return None

    def _fetch():
        client = Client(account_sid, auth_token)
        return client.calls(call_sid).fetch()

    try:
        call = await asyncio.to_thread(_fetch)
        
        return CallInfo(from_number=call._from, to_number=call.to, forwarded_from=call.forwarded_from)
    except Exception as e:
        logger.error(f"Error fetching call info from Twilio: {e}")
        return None