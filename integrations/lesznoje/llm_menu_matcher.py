import json
from typing import Dict, List, Any, Optional

from integrations.lesznoje.lesznoje_api import get_restaurant_details
from integrations.lesznoje.menu_parser import dd
from models import Menu


def convert_llm_output_to_api_format(
    llm_output: Dict[str, Any],
    parsed_menu: Menu,
    original_menu: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Convert LLM output format to restaurant API format

    LLM output format:
    {
        "customer_name": "Customer name from conversation",
        "products": [
            {
                "product_id": "product_id",
                "variant_id": "variant_id",
                "addons": ["addon_id"],
                "name": "Product name"
            }
        ]
    }

    Restaurant API format:
    [
        {
            "desc": "z cynamonem, warzywami i ry\u017cem",
            "name": "Kaczka w sosie a'la szef",
            "price": 55,
            "additionalFields": [],
            "category": "Kaczka - specjalno\u015b\u0107 szefa kuchni Khone",
            "amount": 1,
            "selectedAdditionalFields": [],
            "notes": ""
        }
    ]
    """
    api_format_products = []

    # Flatten the nested structure - get all items from all addon sets
    global_additional_items = [
        item 
        for addon in original_menu['addonFieldsSets'] 
        for item in addon["items"]
    ]
    


    for llm_product in llm_output.get("products", []):
        product_id = llm_product.get("product_id")
        variant_id = llm_product.get("variant_id")
        addon_ids = llm_product.get("addons", [])

        # Use Menu model methods instead of manual lookups
        product_result = parsed_menu.find_product_by_id(product_id)
        if not product_result:
            continue

        category, product = product_result
        category_name = category.name

        variant = product.find_variant_by_id(variant_id) if variant_id else None

        # Find selected addons using the product model
        selected_additional_fields = []
        for addon_id in addon_ids:
            addon_result = product.find_addon_value_by_id(addon_id)
            if addon_result:
                addon, addon_value = addon_result
                selected_additional_fields.append({
                    "id": addon_id,
                    "name": addon_value.name,
                    "group_name": addon.name
                })
        api_product = {
            "desc": product.product_description or "",
            "priceOptions": [{"name": v.name, "price": v.price, "variant_id": v.variant_id} for v in product.product_variants],
            "name": product.product_name + (" " + variant.name if variant else ""),
            "price": variant.price if variant else product.product_price or 0,
            "additionalFields": global_additional_items,
            "category": category_name,
            "option": variant.name if variant else "",
            "amount": llm_product.get("amount_ordered", 1),  # Default amount
            "selectedAdditionalFields": [],
            "notes": "",
        }

        if len(selected_additional_fields) > 0:
            grouped_addons = {}
            for addon in selected_additional_fields:
                group_name = addon['group_name']
                if group_name not in grouped_addons:
                    grouped_addons[group_name] = []
                grouped_addons[group_name].append(addon['name'])
            
            formatted_addons = []
            for group_name, addon_names in grouped_addons.items():
                addon_list = ", 1x".join(addon_names)
                formatted_addons.append(f"{group_name}: 1x{addon_list}")
            
            api_product["selectedAdditionalFields"] = formatted_addons
        
        api_format_products.append(api_product)

    return api_format_products


# Manual lookup functions removed - replaced with Menu model methods


def parse_llm_output_to_api_format(llm_output_json: str, parsed_menu: Menu, original_menu_json: str) -> str:
    """Parse LLM output to restaurant API format"""
    try:
        llm_output = json.loads(llm_output_json)
        original_menu = get_restaurant_details()
        
        api_format_products = convert_llm_output_to_api_format(llm_output, parsed_menu, original_menu["menu"])

        return json.dumps(api_format_products, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
