from typing import Dict, List, Any
from models import Menu, Product
from integrations.lesznoje.leszno_menu_to_our import ADDITIONAL_FIELDS_TYPE_SET


def our_products_to_leszno_api_format(
    our_products: Dict[str, Any],
    parsed_menu: Menu,
    original_menu: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Convert OUR products format to restaurant API format

    OUR output format:
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

    global_additional_items = original_menu["addonFieldsSets"]

    for our_product in our_products.get("products", []):
        product_id = our_product.get("product_id")
        variant_id = our_product.get("variant_id")
        addon_ids = our_product.get("addons", [])

        product_result = parsed_menu.find_product_by_id(product_id)
        if not product_result:
            continue

        category, product = product_result
        category_name = category.name

        variant = product.find_variant_by_id(variant_id) if variant_id else None

        api_product = {
            "desc": product.product_description or "",
            "priceOptions": [{"name": v.name, "price": v.price, "variant_id": v.variant_id} for v in product.product_variants],
            "name": product.product_name + (" " + variant.name if variant else ""),
            "price": variant.price if variant else product.product_price or 0,
            "category": category_name,
            "amount": our_product.get("amount_ordered", 1),
            "selectedAdditionalFields": [],
            "notes": "",
        }

        set_addon_reference_ids = [addon.reference_id for addon in product.product_addons if addon.type == ADDITIONAL_FIELDS_TYPE_SET and addon.reference_id]

        matching_global_addons = [global_addon for global_addon in global_additional_items if global_addon.get("id") in set_addon_reference_ids]

        if matching_global_addons:
            api_product["additionalFields"] = [item for global_addon in matching_global_addons for item in global_addon.get("items", [])]
        else:
            api_product["additionalFields"] = [
                {"name": addon.name, "type": addon.type, "price": addon.price, "values": [{"name": value.name, "id": value.addon_id} for value in addon.values]}
                for addon in product.product_addons
                if addon.type != ADDITIONAL_FIELDS_TYPE_SET
            ]

        if variant:
            api_product["option"] = variant.name

        selected_additional_fields = []
        for addon_id in addon_ids:
            addon_result = product.find_addon_value_by_id(addon_id)
            if addon_result:
                addon, addon_value = addon_result
                selected_additional_fields.append({"our_id": addon_id, "name": addon_value.name, "group_name": addon.name})

        if len(selected_additional_fields) > 0:
            grouped_addons = {}
            for addon in selected_additional_fields:
                group_name = addon["group_name"]
                if group_name not in grouped_addons:
                    grouped_addons[group_name] = []
                grouped_addons[group_name].append(addon["name"])

            formatted_addons = []
            for group_name, addon_names in grouped_addons.items():
                addon_list = ", 1x".join(addon_names)
                formatted_addons.append(f"{group_name}: 1x{addon_list}")

            api_product["selectedAdditionalFields"] = formatted_addons

        api_format_products.append(api_product)

    return api_format_products
