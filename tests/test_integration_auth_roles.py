import pytest

from app.services.store_app_service import StoreAppService
from app.db import connection as conn_mod
from app.db.schema import init_db


@pytest.fixture
def app(tmp_path, monkeypatch):
    # point DB to a temp file
    monkeypatch.setattr(conn_mod, "DATA_DIR", tmp_path, raising=True)
    monkeypatch.setattr(conn_mod, "DB_PATH", tmp_path / "omnistore_test.db", raising=True)

    init_db()
    return StoreAppService.create_default()


@pytest.mark.integration
def test_register_and_login_customer_creates_customer_and_cart(app):
    r = app.ui_register_customer(
        username="cust1",
        email="cust1@local.test",
        name="Customer One",
        password="pass123",
        currency="EUR",
    )
    assert r.ok, r.error.message

    user = r.data
    assert user is not None
    assert getattr(user, "id", None) is not None

    # Login should work
    lr = app.ui_login(email="cust1@local.test", password="pass123")
    assert lr.ok, lr.error.message
    logged = lr.data
    assert logged.email == "cust1@local.test"
    assert getattr(logged, "role", None) == "CUSTOMER"

    # Verify DB side-effects: Customer row exists + Cart row exists
    conn = conn_mod.get_connection()
    try:
        row_c = conn.execute('SELECT UserID, Currency FROM "Customer" WHERE UserID = ?', (int(user.id),)).fetchone()
        assert row_c is not None
        assert row_c["Currency"] == "EUR"

        row_cart = conn.execute('SELECT ID FROM "Cart" WHERE CustomerUserID = ?', (int(user.id),)).fetchone()
        assert row_cart is not None
    finally:
        conn.close()
