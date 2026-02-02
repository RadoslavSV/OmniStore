from app.presentation.dto import cart_dto


def test_cart_dto_maps_structure_correctly():
    cart = {
        "items": [
            {
                "item_id": 1,
                "name": "Office Desk",
                "quantity": 2,
                "unit_price": 300.0,
                "subtotal": 600.0,
                "currency": "EUR",
            }
        ],
        "total": {
            "total": 600.0,
            "currency": "EUR",
        },
    }

    dto = cart_dto(cart)

    assert "items" in dto
    assert "total" in dto

    assert len(dto["items"]) == 1
    item = dto["items"][0]

    assert item["item_id"] == 1
    assert item["name"] == "Office Desk"
    assert item["quantity"] == 2
    assert item["unit_price"] == 300.0
    assert item["subtotal"] == 600.0
    assert item["currency"] == "EUR"

    assert dto["total"]["amount"] == 600.0
    assert dto["total"]["currency"] == "EUR"
