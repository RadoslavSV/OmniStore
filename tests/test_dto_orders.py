from app.presentation.dto import order_list_dto


def test_order_list_dto_maps_orders_correctly():
    orders = [
        {
            "order_id": 100,
            "created_at": "2025-01-01T10:00:00Z",
            "status": "PAID",
            "total_base": 480.0,
            "currency": "EUR",
        }
    ]

    dto = order_list_dto(orders)

    assert isinstance(dto, list)
    assert len(dto) == 1

    order = dto[0]
    assert order["order_id"] == 100
    assert order["status"] == "PAID"
    assert order["total"] == 480.0
    assert order["currency"] == "EUR"
