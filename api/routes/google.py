from __future__ import annotations

from fastapi import APIRouter, Query, HTTPException, Depends
from datetime import datetime
import logging

from providers.google_api import search_contacts, get_calendar_events
from api.dependencies import get_logger, validate_date_format

router = APIRouter(prefix="/google", tags=["google"])


@router.get("/contacts/search")
async def google_contacts_search(
    query: str = Query(..., description="Search query for contacts"),
    max_results: int = Query(10, description="Maximum number of results to return"),
    logger: logging.Logger = Depends(get_logger)
):
    """Search Google contacts by query string."""
    contacts = search_contacts(query, max_results)
    logger.info(f"Found {len(contacts)} contacts for query: {query}")
    return {"contacts": contacts, "count": len(contacts)}


@router.get("/calendar/events")
async def google_calendar_events(
    start_date: str = Query(..., description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date in ISO format (YYYY-MM-DD)"),
    calendar_id: str = Query("primary", description="Calendar ID (default: primary)"),
    max_results: int = Query(10, description="Maximum number of results to return"),
    logger: logging.Logger = Depends(get_logger)
):
    """Get Google Calendar events within a specified date range."""
    try:
        # Validate date formats
        validate_date_format(start_date)
        validate_date_format(end_date)
        
        # Parse date strings to datetime objects
        start_datetime = datetime.fromisoformat(start_date)
        end_datetime = datetime.fromisoformat(end_date)

        # Get calendar events
        events = get_calendar_events(
            start_time=start_datetime,
            end_time=end_datetime,
            calendar_id=calendar_id,
            max_results=max_results
        )

        logger.info(f"Retrieved {len(events)} calendar events from {start_date} to {end_date}")
        return {"events": events, "count": len(events)}
        
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error retrieving calendar events: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving calendar events: {str(e)}")
