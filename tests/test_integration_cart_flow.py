import pytest

from app.services.store_app_service import StoreAppService
from app.db import connection as conn_mod
from app.db.schema import init_db


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(conn_mod, "DATA_DIR", tmp_path, raising=True)
    monkeypatch.setattr(conn_mod, "DB_PATH", tmp_path / "omnistore_test.db", raising=True)
    init_db()
    return StoreAppService.create_default()


def _make_admin_and_customer(app):
    ar = app.ui_register_customer("admin1", "admin1@local.test", "Admin One", "admin123", "EUR")
    assert ar.ok, ar.error.message
    admin_user = ar.data
    app.ensure_admin(int(admin_user.id))

    cr = app.ui_register_customer("cust1", "cust1@local.test", "Customer One", "pass123", "EUR")
    assert cr.ok, cr.error.message
    cust_user = cr.data
    return int(admin_user.id), int(cust_user.id)


def _insert_item(admin_user_id: int, name: str, price: float) -> int:
    conn = conn_mod.get_connection()
    try:
        cur = conn.execute(
            """
            INSERT INTO "Item"(AdminUserID, Name, Description, Height, Width, Depth, Weight, Price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (admin_user_id, name, f"{name} desc", 10.0, 10.0, 10.0, 1.0, float(price)),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


@pytest.mark.integration
def test_cart_add_update_remove_updates_db_and_service_reads(app):
    admin_id, cust_id = _make_admin_and_customer(app)

    item1 = _insert_item(admin_id, "Desk", 300.0)
    item2 = _insert_item(admin_id, "Lamp", 40.0)

    # Add to cart (service -> repos -> DB)
    r1 = app.ui_add_to_cart(cust_id, item_id=item1, quantity=1)
    assert r1.ok, r1.error.message
    r2 = app.ui_add_to_cart(cust_id, item_id=item2, quantity=2)
    assert r2.ok, r2.error.message

    cart = app.ui_get_cart(cust_id, display_currency="EUR")
    assert cart.ok, cart.error.message
    data = cart.data
    assert len(data["items"]) == 2

    # Update quantity
    q = app.cart.set_quantity(cust_id, item_id=item1, quantity=3)
    assert q is None  # method returns None on success

    cart2 = app.ui_get_cart(cust_id, display_currency="EUR")
    assert cart2.ok
    rows = {int(x["item_id"]): x for x in cart2.data["items"]}
    assert rows[item1]["quantity"] == 3
    assert rows[item2]["quantity"] == 2

    # Remove
    rr = app.ui_remove_from_cart(cust_id, item_id=item2)
    assert rr.ok

    cart3 = app.ui_get_cart(cust_id, display_currency="EUR")
    assert cart3.ok
    ids = [int(x["item_id"]) for x in cart3.data["items"]]
    assert ids == [item1]
