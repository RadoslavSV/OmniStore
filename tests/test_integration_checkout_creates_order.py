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
def test_checkout_creates_order_items_and_clears_cart(app):
    admin_id, cust_id = _make_admin_and_customer(app)

    desk_id = _insert_item(admin_id, "Desk", 300.0)
    lamp_id = _insert_item(admin_id, "Lamp", 40.0)

    assert app.ui_add_to_cart(cust_id, item_id=desk_id, quantity=2).ok
    assert app.ui_add_to_cart(cust_id, item_id=lamp_id, quantity=1).ok

    # Checkout (service -> repos -> DB)
    ch = app.ui_checkout(cust_id)
    assert ch.ok, ch.error.message
    order_id = int(ch.data)

    conn = conn_mod.get_connection()
    try:
        # Order exists
        o = conn.execute('SELECT ID, CustomerUserID, TotalBase FROM "Order" WHERE ID = ?', (order_id,)).fetchone()
        assert o is not None
        assert int(o["CustomerUserID"]) == cust_id
        # TotalBase: 2*300 + 1*40 = 640
        assert float(o["TotalBase"]) == 640.0

        # Order items exist (snapshot)
        rows = conn.execute('SELECT ItemName, UnitPriceBase, Quantity FROM "OrderItem" WHERE OrderID = ?', (order_id,)).fetchall()
        assert len(rows) == 2
        got = sorted([(r["ItemName"], float(r["UnitPriceBase"]), int(r["Quantity"])) for r in rows])
        assert got == [("Desk", 300.0, 2), ("Lamp", 40.0, 1)]

        # Cart cleared
        cart = conn.execute('SELECT ID FROM "Cart" WHERE CustomerUserID = ?', (cust_id,)).fetchone()
        assert cart is not None
        cart_id = int(cart["ID"])
        left = conn.execute('SELECT 1 FROM "Item_Cart" WHERE CartID = ? LIMIT 1', (cart_id,)).fetchone()
        assert left is None
    finally:
        conn.close()
