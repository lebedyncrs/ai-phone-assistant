
import asyncio
import os

from loguru import logger
from twilio.rest import Client

async def get_call_info(call_sid: str) -> dict:
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        logger.warning("Missing Twilio credentials, cannot fetch call info")
        return {}

    def _fetch():
        client = Client(account_sid, auth_token)
        return client.calls(call_sid).fetch()

    try:
        call = await asyncio.to_thread(_fetch)
        
        return {
            "from_number": call._from,
            "to_number": call.to,
        }
    except Exception as e:
        logger.error(f"Error fetching call info from Twilio: {e}")
        return {}