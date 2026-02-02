from app.presentation.dto import item_list_dto

def test_item_list_dto_maps_fields_correctly():
    items = [
        {
            "item_id": 10,
            "name": "Office Desk",
            "price_base": 300.0,
            "price": 355.6,
            "currency": "USD",
        },
        {
            "item_id": 11,
            "name": "Desk Lamp",
            "price_base": 40.0,
            "price": 47.4,
            "currency": "USD",
        },
    ]

    dto = item_list_dto(items)

    assert isinstance(dto, list)
    assert len(dto) == 2

    assert dto[0]["id"] == 10
    assert dto[0]["name"] == "Office Desk"
    assert dto[0]["currency"] == "USD"
    assert dto[0]["price"] == 355.6
    
    assert dto[1]["id"] == 11
    assert dto[1]["name"] == "Desk Lamp"
    assert dto[1]["currency"] == "USD"
    assert dto[1]["price"] == 47.4
