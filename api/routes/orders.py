from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
import logging
import json

from providers.twilio_api import get_latest_call
from providers.open_ai import match_ordered_products
from integrations.lesznoje.lesznoje_api import get_restaurant_details, create_order
from integrations.lesznoje.leszno_menu_to_our import leszno_menu_to_our
from integrations.lesznoje.our_menu_to_leszno import our_products_to_leszno_api_format
from api.dependencies import get_logger

router = APIRouter(tags=["orders"])


@router.post("/vapi/call-ended")
async def call_end(data: list = Body(...), logger: logging.Logger = Depends(get_logger)):
    """Process order from VAPI call transcript."""
    try:
        conversation_transcript = data[0]["message"]["transcript"]
        logger.info("Processing order from call transcript")

        # Get menu data and parse it
        menu = get_restaurant_details()["menu"]
        parsed_menu = leszno_menu_to_our(menu)
        logger.info("Retrieved and parsed restaurant menu")

        # For development, use stored LLM response
        # In production, uncomment these lines to use the actual LLM
        # matched_ordered_products = match_ordered_products(json.dumps(parsed_menu), conversation_transcript)
        # llm_response_json = matched_ordered_products

        # Read the stored LLM response for testing
        with open("storage/llm_response.json", "r") as f:
            llm_response_json = f.read()

        leszno_products_format = our_products_to_leszno_api_format(json.loads(llm_response_json), parsed_menu, menu)

        latest_call = get_latest_call()

        order_data = {
            "customer": {
                "customer_firstname": json.loads(llm_response_json)["customer_name"],
                "phone": latest_call["from_formatted"],
                "flat": "",
                "cutleryPreferences": "",
                "notes": "Voice agent order",
                "delivery": "takeout",
                "allowMarketing": False,
                "allowSms": False,
                "allowEmail": False,
                "deliveryAt": "",
            },
            "products": leszno_products_format,
            "payment_type": "card_on_place",
            "delivery_type": "takeout",
            "source": "web_app",
            "price": sum([product["price"] for product in leszno_products_format]),
            "delivery_cost": 0,
        }

        order_response = create_order(order_data)
        logger.info(f"Order created successfully: {order_response}")

        return {"message": order_data}

    except FileNotFoundError:
        logger.error("LLM response file not found")
        raise HTTPException(status_code=500, detail="LLM response file not found")
    except KeyError as e:
        logger.error(f"Missing required data in request: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Missing required data: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing order: {str(e)}")
