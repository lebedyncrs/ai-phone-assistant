from fastapi import FastAPI, Query, Path, HTTPException, Request, Depends, status
from fastapi.responses import RedirectResponse
import uvicorn
from datetime import datetime
from typing import Optional
import os

from providers.twilio_api import get_latest_call
from providers.google_api import search_contacts, get_calendar_events

app = FastAPI(title="Personal Voice Assistant API", description="A FastAPI application for a personal voice assistant", version="0.1.0")


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/twilio/latest-call")
async def latest_call():
    latest_call = get_latest_call()
    return {"latest_call": latest_call}

@app.get("/twilio/who-is-calling")
async def who_is_calling():
    latest_call = get_latest_call()
    if latest_call.get("status") == "completed" or latest_call.get("direction") != "inbound":
        return {"caller": None}
    
    contacts = search_contacts(latest_call["from_formatted"][3:],1)
    return {"caller": contacts[0] if contacts else None}



@app.get("/google/contacts/search")
async def google_contacts_search(
    query: str = Query(..., description="Search query for contacts"), max_results: int = Query(10, description="Maximum number of results to return")
):
    contacts = search_contacts(query, max_results)
    return {"contacts": contacts, "count": len(contacts)}


@app.get("/google/calendar/events")
async def google_calendar_events(
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DD)"),
    calendar_id: str = Query("primary", description="Calendar ID (default: primary)"),
    max_results: int = Query(10, description="Maximum number of results to return"),
):
    """
    Get Google Calendar events within a specified date range
    """
    try:
        # Parse date strings to datetime objects
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)

        # Get calendar events
        events = get_calendar_events(start_time=start_datetime, end_time=end_datetime, calendar_id=calendar_id, max_results=max_results)

        return {"events": events, "count": len(events)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving calendar events: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
