import requests


def get_restaurant_details(restaurant_id: int = 521) -> dict:
    response = requests.get(f"https://otostolik.pl/api/restaurants/{restaurant_id}")
    return {
        "menu": response.json()["menu"],
        "name": response.json()["name"],
        "location": response.json()["location"],
        "status": response.json()["status"],
        "phone": response.json()["phone"],
    }


def create_order(order_data: dict) -> dict:
    # return {}
    return requests.post("https://api.otostolik.pl/api/restaurants/124/orders", json=order_data).json()
