from typing import List, Dict


# ---------- ITEM ----------

def item_list_dto(items) -> List[Dict]:
    return [
        {
            "id": it["item_id"],
            "name": it["name"],
            # IMPORTANT: use converted "price" if present; fallback to base
            "price": it.get("price", it.get("price_base")),
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
            # Keep existing structure (your services return total["total"])
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
            # IMPORTANT: prefer converted total if present; fallback to base
            "total": o.get("total", o.get("total_base")),
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
            "total": details["order"].get("total", details["order"].get("total_base")),
            "currency": details["order"]["currency"],
        },
        "items": [
            {
                "item_id": it["item_id"],
                "name": it["item_name"],
                "quantity": it["quantity"],
                "unit_price": it.get("unit_price", it.get("unit_price_base")),
                "subtotal": it.get("subtotal", it.get("subtotal_base")),
                "currency": it["currency"],
            }
            for it in details["items"]
        ],
    }


# ---------- ITEM DETAILS ----------

def item_details_dto(details: Dict) -> Dict:
    it = details["item"]
    return {
        "id": it.id,
        "name": it.name,
        "description": it.description,
        "dimensions": {
            "length": float(it.dimensions.length),
            "width": float(it.dimensions.width),
            "height": float(it.dimensions.height),
        },
        "weight": float(it.weight),
        "price": float(it.price),
        "currency": "EUR",
        "categories": details.get("categories", []),
        "pictures": details.get("pictures", []),
        "main_picture": details.get("main_picture"),
    }
