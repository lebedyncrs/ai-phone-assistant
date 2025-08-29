import json
import unicodedata
import hashlib

MULTIPLE_CHOICE_TYPE = "multiple-choice"
ADDITIONAL_FIELDS_TYPE_SET = "set"


def remove_polish_chars(text) -> str:
    """
    Remove Polish diacritical marks from text
    """
    normalized = unicodedata.normalize("NFD", text)
    return "".join([c for c in normalized if not unicodedata.combining(c)])

def short_stable_hash(value: str, length: int = 8) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:length]


def parse_menu_for_llm(menu_data: dict) -> dict:
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
            if 'price' in product:
                new_product["product_price"] = product["price"]
            
            if "additionalFields" in product and product["additionalFields"]:
                for additional_field in product["additionalFields"]:
                    if additional_field["type"] == ADDITIONAL_FIELDS_TYPE_SET and additional_field["value"] in new_global_product_addons:
                        new_product["product_addons"] = new_global_product_addons[additional_field["value"]]
                

            new_category["products"].append(new_product)
        parsed_menu["categories"].append(new_category)
       
    return parsed_menu


def parse_product_variants(product: dict) -> list:
    product_variants = []
    if "priceOptions" not in product or not product["priceOptions"]:
        return product_variants

    for variant in product["priceOptions"]:
        product_variant_id = short_stable_hash(variant["name"])
        product_variants.append(
            {
                "name": variant["name"],
                "price": variant["price"],
                "variant_id": product_variant_id,
            }
        )

    return product_variants


def parse_global_product_addons(menu: dict) -> list:
    new_global_product_addons = {}

    if "addonFieldsSets" not in menu or not menu["addonFieldsSets"]:
        return new_global_product_addons

    global_product_addons = menu["addonFieldsSets"]

    for addon in global_product_addons:
        if not addon["items"] or addon["items"][0]["type"] != MULTIPLE_CHOICE_TYPE:
            continue

        addon_types = []
        for value in addon["items"][0]["value"].split(", "):
            addon_types.append({"addon_id": short_stable_hash(value), "name": value})

        new_global_product_addons[addon["id"]] = {
            "name": addon["name"],
            "values": addon_types,
        }
    return new_global_product_addons

def dd(obj):
    print(json.dumps(obj, indent=2, default=str))
    exit()
    
    
def parse_menu_from_llm(menu_data: dict) -> dict:
    return menu_data


if __name__ == "__main__":
    with open("storage/menu.json", "r") as f:
        menu_data = json.load(f)
        parsed_menu = parse_menu(menu_data)
        with open("storage/parsed_menu.json", "w") as f:
            json.dump(parsed_menu, f, indent=2, default=str)
