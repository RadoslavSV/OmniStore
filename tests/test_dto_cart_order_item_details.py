from app.presentation.dto import cart_dto, order_list_dto, order_details_dto, item_details_dto


# ---------------- Cart DTO ----------------

def test_cart_dto_maps_items_and_total_correctly():
    cart = {
        "items": [
            {
                "item_id": 1,
                "name": "Desk",
                "quantity": 2,
                "unit_price": 355.6,
                "subtotal": 711.2,
                "currency": "USD",
            }
        ],
        "total": {"total": 711.2, "currency": "USD"},
    }

    dto = cart_dto(cart)

    assert dto["total"]["amount"] == 711.2
    assert dto["total"]["currency"] == "USD"

    assert len(dto["items"]) == 1
    assert dto["items"][0]["item_id"] == 1
    assert dto["items"][0]["name"] == "Desk"
    assert dto["items"][0]["quantity"] == 2
    assert dto["items"][0]["unit_price"] == 355.6
    assert dto["items"][0]["subtotal"] == 711.2
    assert dto["items"][0]["currency"] == "USD"


def test_cart_dto_handles_empty_items_list():
    cart = {"items": [], "total": {"total": 0.0, "currency": "EUR"}}
    dto = cart_dto(cart)

    assert dto["items"] == []
    assert dto["total"]["amount"] == 0.0
    assert dto["total"]["currency"] == "EUR"


# ---------------- Order List DTO ----------------

def test_order_list_dto_prefers_converted_total_if_present():
    orders = [
        {
            "order_id": 10,
            "created_at": "2026-01-01T10:00:00Z",
            "status": "CREATED",
            "total_base": 300.0,
            "total": 355.6,
            "currency": "USD",
        }
    ]

    dto = order_list_dto(orders)

    assert dto[0]["order_id"] == 10
    assert dto[0]["total"] == 355.6
    assert dto[0]["currency"] == "USD"


def test_order_list_dto_falls_back_to_total_base():
    orders = [
        {
            "order_id": 11,
            "created_at": "2026-01-01T10:00:00Z",
            "status": "CREATED",
            "total_base": 180.0,
            "currency": "EUR",
        }
    ]

    dto = order_list_dto(orders)
    assert dto[0]["total"] == 180.0
    assert dto[0]["currency"] == "EUR"


# ---------------- Order Details DTO ----------------

def test_order_details_dto_maps_order_and_items_prefers_converted_fields():
    details = {
        "order": {
            "order_id": 5,
            "created_at": "2026-01-01T10:00:00Z",
            "status": "CREATED",
            "total_base": 300.0,
            "total": 355.6,
            "currency": "USD",
        },
        "items": [
            {
                "item_id": 1,
                "item_name": "Desk",
                "quantity": 2,
                "unit_price_base": 300.0,
                "subtotal_base": 600.0,
                "unit_price": 355.6,
                "subtotal": 711.2,
                "currency": "USD",
            }
        ],
    }

    dto = order_details_dto(details)

    assert dto["order"]["order_id"] == 5
    assert dto["order"]["total"] == 355.6
    assert dto["order"]["currency"] == "USD"

    assert len(dto["items"]) == 1
    assert dto["items"][0]["name"] == "Desk"
    assert dto["items"][0]["unit_price"] == 355.6
    assert dto["items"][0]["subtotal"] == 711.2


def test_order_details_dto_falls_back_to_base_fields():
    details = {
        "order": {
            "order_id": 6,
            "created_at": "2026-01-01T10:00:00Z",
            "status": "CREATED",
            "total_base": 180.0,
            "currency": "EUR",
        },
        "items": [
            {
                "item_id": 2,
                "item_name": "Lamp",
                "quantity": 1,
                "unit_price_base": 40.0,
                "subtotal_base": 40.0,
                "currency": "EUR",
            }
        ],
    }

    dto = order_details_dto(details)

    assert dto["order"]["total"] == 180.0
    assert dto["items"][0]["unit_price"] == 40.0
    assert dto["items"][0]["subtotal"] == 40.0


# ---------------- Item Details DTO ----------------

class _Dims:
    def __init__(self, length, width, height):
        self.length = length
        self.width = width
        self.height = height

class _Item:
    def __init__(self):
        self.id = 7
        self.name = "Office Desk"
        self.description = "Wood desk"
        self.dimensions = _Dims(120.0, 60.0, 75.0)
        self.weight = 25.5
        self.price = 300.0

def test_item_details_dto_maps_item_structure():
    details = {
        "item": _Item(),
        "categories": ["Office", "Furniture"],
        "pictures": ["images/desk_1.png"],
        "main_picture": "images/desk_1.png",
    }

    dto = item_details_dto(details)

    assert dto["id"] == 7
    assert dto["name"] == "Office Desk"
    assert dto["dimensions"]["length"] == 120.0
    assert dto["dimensions"]["width"] == 60.0
    assert dto["dimensions"]["height"] == 75.0
    assert dto["weight"] == 25.5
    assert dto["price"] == 300.0
    assert dto["currency"] == "EUR"
    assert dto["categories"] == ["Office", "Furniture"]
    assert dto["pictures"] == ["images/desk_1.png"]
    assert dto["main_picture"] == "images/desk_1.png"
