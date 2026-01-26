from typing import List, Dict


# ---------- ITEM ----------

def item_list_dto(items) -> List[Dict]:
    return [
        {
            "id": it["item_id"],
            "name": it["name"],
            "price": it["price_base"],
            "currency": it["currency"],
        }
        for it in items
    ]


# ---------- CART ----------

def cart_dto(cart: Dict) -> Dict:
    return {
        "items": [
            {
                "item_id": it["item_id"],
                "name": it["name"],
                "quantity": it["quantity"],
                "unit_price": it["unit_price"],
                "subtotal": it["subtotal"],
                "currency": it["currency"],
            }
            for it in cart.get("items", [])
        ],
        "total": {
            "amount": cart["total"]["total"],
            "currency": cart["total"]["currency"],
        },
    }


# ---------- ORDER ----------

def order_list_dto(orders: List[Dict]) -> List[Dict]:
    return [
        {
            "order_id": o["order_id"],
            "created_at": o["created_at"],
            "status": o["status"],
            "total": o["total_base"],
            "currency": o["currency"],
        }
        for o in orders
    ]


def order_details_dto(details: Dict) -> Dict:
    return {
        "order": {
            "order_id": details["order"]["order_id"],
            "created_at": details["order"]["created_at"],
            "status": details["order"]["status"],
            "total": details["order"]["total_base"],
            "currency": details["order"]["currency"],
        },
        "items": [
            {
                "item_id": it["item_id"],
                "name": it["item_name"],
                "quantity": it["quantity"],
                "unit_price": it["unit_price_base"],
                "subtotal": it["subtotal_base"],
                "currency": it["currency"],
            }
            for it in details["items"]
        ],
    }
