import json
import unicodedata
import hashlib
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Menu

MULTIPLE_CHOICE_TYPE = "multiple-choice"
ADDITIONAL_FIELDS_TYPE_SET = "set"  # means we have to reference global 'addonFieldsSets'
CHECKBOX_TYPE = "checkbox"


def remove_polish_chars(text) -> str:
    """
    Remove Polish diacritical marks from text
    """
    normalized = unicodedata.normalize("NFD", text)
    return "".join([c for c in normalized if not unicodedata.combining(c)])


def short_stable_hash(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def leszno_menu_to_our(menu_data: dict) -> Menu:
    """Convert restaurant API format to our internal Menu Pydantic model."""
    parsed_menu = {"categories": []}
    new_global_product_addons = parse_global_product_addons(menu_data)
    for category in menu_data["categories"]:
        category_name = category["name"]
        category_id = short_stable_hash(category_name)
        new_category = {"id": category_id, "name": category_name, "products": []}

        for product in category["items"]:
            new_product = {"category_id": category_id}
            if product["isDisabled"]:
                continue

            product_id = short_stable_hash(product["name"])
            product_variants = parse_product_variants(product)

            new_product["product_id"] = product_id
            new_product["product_name"] = product["name"]
            new_product["product_description"] = product["desc"]
            new_product["product_variants"] = product_variants
            new_product["product_addons"] = []
            if "price" in product:
                new_product["product_price"] = product["price"]

            if "additionalFields" in product and product["additionalFields"]:
                for additional_field in product["additionalFields"]:
                    if "value" in additional_field and additional_field["value"] in new_global_product_addons:
                        new_product["product_addons"].append(new_global_product_addons[additional_field["value"]])

            new_category["products"].append(new_product)
        parsed_menu["categories"].append(new_category)

    return Menu.from_dict(parsed_menu)


def parse_product_variants(product: dict) -> list:
    if "priceOptions" not in product or not product["priceOptions"]:
        return []

    return [
        {
            "name": variant["name"],
            "price": variant["price"],
            "variant_id": short_stable_hash(variant["name"]),
        }
        for variant in product["priceOptions"]
    ]


def parse_global_product_addons(menu: dict) -> dict:
    if "addonFieldsSets" not in menu or not menu["addonFieldsSets"]:
        return {}

    global_product_addons = {}

    for addon in menu["addonFieldsSets"]:
        if not addon["items"]:
            continue

        first_item = addon["items"][0]
        is_for_free = "addonPrice" not in addon["items"][0]
        if first_item["type"] == MULTIPLE_CHOICE_TYPE:
            addon_values = [
                {
                    "addon_id": short_stable_hash(value.strip()),
                    "name": value.strip(),
                    "group_name": addon["name"],
                }
                for value in first_item["value"].split(", ")
            ]
        elif first_item["type"] == ADDITIONAL_FIELDS_TYPE_SET:
            continue  ## have to be implemented
        elif first_item["type"] == CHECKBOX_TYPE:
            continue  ## have to be implemented

        global_product_addons[addon["id"]] = {
            "name": first_item["name"],
            "values": addon_values,
            "is_for_free": is_for_free,
        }

    return global_product_addons


def dd(obj):
    print(json.dumps(obj, indent=2, default=str))
    exit()


def parse_menu_from_llm(menu_data: dict) -> dict:
    return menu_data


if __name__ == "__main__":
    with open("storage/menu.json", "r") as f:
        menu_data = json.load(f)
        parsed_menu = leszno_menu_to_our(menu_data)
        with open("storage/parsed_menu.json", "w") as f:
            json.dump(parsed_menu.model_dump(), f, indent=2, default=str)
