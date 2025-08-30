from __future__ import annotations

from fastapi import APIRouter, Depends
import logging

from providers.twilio_api import get_latest_call
from providers.google_api import search_contacts
from api.dependencies import get_logger

router = APIRouter(prefix="/twilio", tags=["twilio"])


@router.get("/latest-call")
async def latest_call(logger: logging.Logger = Depends(get_logger)):
    """Get the latest Twilio call information."""
    latest_call = get_latest_call()
    logger.info("Retrieved latest call information")
    return {"latest_call": latest_call}


@router.get("/who-is-calling")
async def who_is_calling(logger: logging.Logger = Depends(get_logger)):
    """Identify who is calling based on the latest inbound call."""
    latest_call = get_latest_call()
    
    if latest_call.get("status") == "completed" or latest_call.get("direction") != "inbound":
        logger.info("No active inbound call found")
        return {"caller": None}

    # Search for contact by phone number (remove country code prefix)
    phone_number = latest_call["from_formatted"][3:]
    contacts = search_contacts(phone_number, 1)
    
    caller = contacts[0] if contacts else None
    logger.info(f"Identified caller: {caller['name'] if caller else 'Unknown'}")
    
    return {"caller": caller}
