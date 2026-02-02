from app.services.store_app_service import StoreAppService


class Dummy:
    pass


def make_app():
    return StoreAppService(
        user_repo=Dummy(),
        admin_repo=Dummy(),
        customer_repo=Dummy(),
        item_repo=Dummy(),
        category_repo=Dummy(),
        item_category_repo=Dummy(),
        picture_repo=Dummy(),
        cart_repo=Dummy(),
        item_cart_repo=Dummy(),
        favorites_repo=Dummy(),
        history_repo=Dummy(),
        order_repo=Dummy(),
        order_item_repo=Dummy(),
        auth=Dummy(),
        roles=Dummy(),
        cart=Dummy(),
        checkout=Dummy(),
        order_history=Dummy(),
        favorites=Dummy(),
        history=Dummy(),
        currency=Dummy(),
        base_currency="EUR",
    )


def test_ui_list_items_filtered_returns_dto_shape(monkeypatch):
    app = make_app()

    # Patch list_items_filtered to avoid DB and currency conversion
    def fake_list_items_filtered(display_currency=None, category_ids=None):
        return [
            {"item_id": 1, "name": "Desk", "price_base": 300.0, "price": 355.6, "currency": "USD"},
            {"item_id": 2, "name": "Lamp", "price_base": 40.0, "price": 47.4, "currency": "USD"},
        ]

    monkeypatch.setattr(app, "list_items_filtered", fake_list_items_filtered)

    res = app.ui_list_items_filtered(display_currency="USD", category_ids=[1, 2])
    assert res.ok is True
    assert isinstance(res.data, list)
    assert res.data[0]["id"] == 1
    assert res.data[0]["name"] == "Desk"
    assert res.data[0]["price"] == 355.6
    assert res.data[0]["currency"] == "USD"
