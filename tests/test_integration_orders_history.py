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
def test_orders_list_and_details_return_expected_snapshot(app):
    admin_id, cust_id = _make_admin_and_customer(app)
    desk_id = _insert_item(admin_id, "Desk", 300.0)

    assert app.ui_add_to_cart(cust_id, item_id=desk_id, quantity=2).ok
    ch = app.ui_checkout(cust_id)
    assert ch.ok
    order_id = int(ch.data)

    # List orders
    lst = app.ui_list_orders(cust_id, limit=10)
    assert lst.ok
    assert len(lst.data) == 1
    assert int(lst.data[0]["order_id"]) == order_id
    assert lst.data[0]["currency"] == "EUR"
    assert float(lst.data[0]["total"]) == 600.0

    # Order details
    det = app.ui_order_details(cust_id, order_id=order_id)
    assert det.ok
    details = det.data
    assert int(details["order"]["order_id"]) == order_id
    assert float(details["order"]["total"]) == 600.0

    assert len(details["items"]) == 1
    assert details["items"][0]["name"] == "Desk"
    assert int(details["items"][0]["quantity"]) == 2
    assert float(details["items"][0]["unit_price"]) == 300.0
    assert float(details["items"][0]["subtotal"]) == 600.0
