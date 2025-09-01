from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Path
import logging
import json
import requests

from providers.twilio_api import get_latest_call
from providers.open_ai import match_ordered_products
from integrations.lesznoje.lesznoje_api import get_restaurant_details, create_order
from integrations.lesznoje.leszno_menu_to_our import leszno_menu_to_our
from integrations.lesznoje.our_menu_to_leszno import our_products_to_leszno_api_format
from api.dependencies import get_logger
from models.menu_model import Menu

router = APIRouter(tags=["orders"])


@router.post("/lesznoje/order")
async def call_end(data: dict = Body(...), logger: logging.Logger = Depends(get_logger)):
    """Process order from VAPI call transcript."""
    try:
        conversation_transcript = data["message"]["transcript"]
        logger.info("Processing order from call transcript")

        # Get menu data and parse it
        menu = get_restaurant_details()["menu"]
        parsed_menu = leszno_menu_to_our(menu)
        logger.info("Retrieved and parsed restaurant menu")

        # For development, use stored LLM response
        # Read the stored LLM response for testing
        # with open("storage/llm_response.json", "r") as f:
        #     matched_ordered_products = f.read()
        # In production, uncomment these lines to use the actual LLM
        matched_ordered_products = match_ordered_products(json.dumps(parsed_menu.model_dump()), conversation_transcript)

        leszno_products_format = our_products_to_leszno_api_format(matched_ordered_products, parsed_menu, menu)

        latest_call = get_latest_call()

        street_name = ""
        street_number = ""
        flat = ""
        if "street" in matched_ordered_products["delivery_address"]:
            street_name = matched_ordered_products["delivery_address"]["street"]
            street_number, flat = matched_ordered_products["delivery_address"]["flat"].split("/")

        order_data = {
            "customer": {
                "customer_firstname": matched_ordered_products["customer_name"],
                "phone": latest_call["from_formatted"],
                "cutleryPreferences": "",
                "notes": "Voice agent order",
                "delivery": matched_ordered_products["delivery_type"],
                "allowMarketing": False,
                "allowSms": False,
                "city": "Leszno",
                "street": street_name,
                "house": street_number,
                "flat": flat,
                "allowEmail": False,
                "deliveryAt": "",
            },
            "products": leszno_products_format,
            "payment_type": matched_ordered_products["payment_type"],
            "delivery_type": matched_ordered_products["delivery_type"],
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


@router.get("/lesznoje/menu/{restaurant_id}", response_model=Menu)
async def get_parsed_menu(restaurant_id: int = Path(..., description="Restaurant ID to fetch menu for"), logger: logging.Logger = Depends(get_logger)) -> Menu:
    """Get parsed menu data by restaurant ID."""
    try:
        logger.info(f"Fetching menu for restaurant ID: {restaurant_id}")

        restaurant_data = get_restaurant_details(restaurant_id)
        parsed_menu = leszno_menu_to_our(restaurant_data["menu"])

        logger.info(f"Successfully parsed menu for restaurant {restaurant_id}")
        return parsed_menu
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch restaurant data: {str(e)}")
        raise HTTPException(status_code=404, detail=f"Restaurant {restaurant_id} not found or API unavailable")
    except KeyError as e:
        logger.error(f"Missing required data in restaurant response: {str(e)}")
        raise HTTPException(status_code=500, detail="Invalid restaurant data format")
    except Exception as e:
        logger.error(f"Error parsing menu for restaurant {restaurant_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing menu: {str(e)}")
