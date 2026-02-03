import pytest

from app.services.store_app_service import StoreAppService
from app.db import connection as conn_mod
from app.db.schema import init_db
from app.db.seed import seed_demo_data_if_empty


@pytest.mark.integration
def test_integration_checkout_creates_order_and_clears_cart(tmp_path, monkeypatch):
    """
    Integration test:
    StoreAppService -> repositories -> sqlite db

    Scenario:
    - init empty DB
    - seed demo data
    - login as demo customer
    - add 2 items to cart
    - checkout
    - assert order exists and cart is empty
    """

    # --- Use isolated test DB (DO NOT touch data/omnistore.db) ---
    test_data_dir = tmp_path / "data"
    test_db_path = test_data_dir / "omnistore_test.db"

    # Patch connection module globals
    monkeypatch.setattr(conn_mod, "DATA_DIR", test_data_dir, raising=True)
    monkeypatch.setattr(conn_mod, "DB_PATH", test_db_path, raising=True)

    # --- Init schema + seed demo data ---
    init_db()
    seed_demo_data_if_empty()

    # --- Create app facade ---
    app = StoreAppService.create_default()

    # --- Login as seeded customer ---
    r_login = app.ui_login("customer@omnistore.local", "customer123")
    assert r_login.ok, r_login.error.message
    customer = r_login.data
    customer_id = int(customer.id)

    # --- Load catalog and pick 2 real item IDs from DB ---
    r_items = app.ui_list_items(display_currency="EUR")
    assert r_items.ok, r_items.error.message
    items = r_items.data
    assert len(items) >= 2

    first_item_id = int(items[0]["id"])
    second_item_id = int(items[1]["id"])

    # --- Add to cart ---
    r_add1 = app.ui_add_to_cart(customer_id, first_item_id, quantity=2)
    assert r_add1.ok, r_add1.error.message

    r_add2 = app.ui_add_to_cart(customer_id, second_item_id, quantity=1)
    assert r_add2.ok, r_add2.error.message

    # --- Checkout ---
    r_checkout = app.ui_checkout(customer_id)
    assert r_checkout.ok, r_checkout.error.message
    order_id = int(r_checkout.data)
    assert order_id > 0

    # --- Verify order appears in order history ---
    r_orders = app.ui_list_orders(customer_id, limit=20)
    assert r_orders.ok, r_orders.error.message
    order_ids = [int(o["order_id"]) for o in (r_orders.data or [])]
    assert order_id in order_ids

    # --- Verify cart is cleared ---
    r_cart = app.ui_get_cart(customer_id, display_currency="EUR")
    assert r_cart.ok, r_cart.error.message
    cart = r_cart.data
    assert cart["items"] == []
    assert float(cart["total"]["amount"]) == 0.0
