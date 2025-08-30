import requests


def get_restaurant_details(restaurant_id: int = 521) -> dict:
    response = requests.get(f"https://otostolik.pl/api/restaurants/{restaurant_id}")
    response.raise_for_status()  # Raise an exception for bad status codes
    data = response.json()
    return {
        "menu": data["menu"],
        "name": data["name"],
        "location": data["location"],
        "status": data["status"],
        "phone": data["phone"],
    }


def create_order(order_data: dict) -> dict:
    # return {}
    return requests.post("https://api.otostolik.pl/api/restaurants/124/orders", json=order_data).json()
