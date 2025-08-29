from fastapi import FastAPI, Query, HTTPException, Body
import uvicorn
from datetime import datetime
import logging
import os
import json

from providers.twilio_api import get_latest_call
from providers.google_api import search_contacts, get_calendar_events
from providers.open_ai import match_ordered_products
from middlewares.middlewares import log_requests
from integrations.lesznoje.lesznoje_api import get_restaurant_details, create_order
from integrations.lesznoje.menu_parser import parse_menu_for_llm
from integrations.lesznoje.llm_menu_matcher import parse_llm_output_to_api_format
from config.logging_config import configure_logging

logger = configure_logging()
app = FastAPI(title="Personal Voice Assistant API", description="A FastAPI application for a personal voice assistant", version="0.1.0")
app.middleware("http")(log_requests)


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

    contacts = search_contacts(latest_call["from_formatted"][3:], 1)
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


@app.post("/vapi/call-ended")
async def call_end(data: list = Body(...)):
    conversation_transcript = data[0]["message"]["transcript"]

    # Get menu data and parse it
    menu = get_restaurant_details()["menu"]
    parsed_menu = parse_menu_for_llm(menu)

    # For development, use stored LLM response
    # In production, uncomment these lines to use the actual LLM
    # matched_ordered_products = match_ordered_products(json.dumps(parsed_menu), conversation_transcript)
    # llm_response_json = matched_ordered_products

    # Read the stored LLM response for testing
    llm_response_json = open("storage/llm_response.json", "r").read()
    api_format_products = parse_llm_output_to_api_format(llm_response_json, json.dumps(parsed_menu))
    order_data = {
        "customer": {
            "customer_name": json.loads(llm_response_json)["customer_name"],
            "phone": get_latest_call()["from_formatted"],
            "flat": "",
            "cutleryPreferences": "",
            "notes": "",
            "delivery": "takeout",
            "allowMarketing": False,
            "allowSms": False,
            "allowEmail": False,
            "deliveryAt": "",
        },
        "products": json.loads(api_format_products),
        "phone": get_latest_call()["from_formatted"],
        "payment_type": "card_on_place",
        "delivery_type": "takeout",
        "source": "web_app",
        "price": sum([product["price"] for product in json.loads(api_format_products)]),
        "delivery_cost": 0,
    }
    order_response = create_order(order_data)

    return {"message": order_data}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
