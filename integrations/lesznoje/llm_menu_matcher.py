import json
from typing import Dict, List, Any, Optional

from integrations.lesznoje.lesznoje_api import get_restaurant_details
from integrations.lesznoje.menu_parser import dd


def convert_llm_output_to_api_format(
    llm_output: Dict[str, Any],
    parsed_menu: Dict[str, Any],
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

        product_info = find_product_by_id(parsed_menu, product_id)
        if not product_info:
            continue

        category_name = find_category_by_product_id(parsed_menu, product_id)
        

        variant_info = find_variant_by_id(product_info, variant_id) if variant_id else None

        selected_additional_fields = find_addons_by_ids(product_info, addon_ids)
        api_product = {
            "desc": product_info.get("product_description", ""),
            "priceOptions": product_info.get("product_variants", []),
            "name": product_info.get("product_name", "") + (" " + variant_info.get("name", "") if variant_info else ""),
            "price": variant_info.get("price", product_info.get("product_price", 0)) if variant_info else product_info.get("product_price", 0),
            "additionalFields": global_additional_items,
            "category": category_name,
            "option": variant_info.get("name", "") if variant_info else "",
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


def find_product_by_id(parsed_menu: Dict[str, Any], product_id: str) -> Optional[Dict[str, Any]]:
    """Find a product in the parsed menu by its ID"""
    for category in parsed_menu.get("categories", []):
        for product in category.get("products", []):
            if product.get("product_id") == product_id:
                return product
    return None


def find_category_name(parsed_menu: Dict[str, Any], category_id: str) -> str:
    """Find a category name by its ID"""
    for category in parsed_menu.get("categories", []):
        if category.get("id") == category_id:
            return category.get("name", "")
    return ""


def find_category_by_product_id(parsed_menu: Dict[str, Any], product_id: str) -> str:
    """Find a category name by product ID"""
    for category in parsed_menu.get("categories", []):
        for product in category.get("products", []):
            if product.get("product_id") == product_id:
                return category.get("name", "")
    return ""


def find_variant_by_id(product_info: Dict[str, Any], variant_id: str) -> Optional[Dict[str, Any]]:
    """Find a variant in a product by its ID"""
    for variant in product_info.get("product_variants", []):
        if variant.get("variant_id") == variant_id:
            return variant
    return None


def find_addons_by_ids(product_info: Dict[str, Any], addon_ids: List[str]) -> List[Dict[str, Any]]:
    """Find addons in a product by their IDs"""
    selected_addons = []

    if "product_addons" not in product_info:
        return selected_addons
    
    for addon_id in addon_ids:
        found = False
        for addon_group in product_info.get("product_addons", []):
            for addon_value in addon_group.get("values", []):
                if addon_value.get("addon_id") == addon_id:
                    selected_addons.append({"id": addon_id, "name": addon_value.get("name", ""), "group_name": addon_group.get("name")})
                    found = True
                    break
            if found:
                break
            
    return selected_addons


def parse_llm_output_to_api_format(llm_output_json: str, parsed_menu_json: str, original_menu_json: str) -> str:
    """Parse LLM output to restaurant API format"""
    try:
        llm_output = json.loads(llm_output_json)
        parsed_menu = json.loads(parsed_menu_json)
        original_menu = get_restaurant_details()
        

        api_format_products = convert_llm_output_to_api_format(llm_output, parsed_menu, original_menu["menu"])

        return json.dumps(api_format_products, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
