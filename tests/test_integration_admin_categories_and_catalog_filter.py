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


def _make_admin(app) -> int:
    ar = app.ui_register_customer("admin1", "admin1@local.test", "Admin One", "admin123", "EUR")
    assert ar.ok, ar.error.message
    admin_user = ar.data
    app.ensure_admin(int(admin_user.id))
    return int(admin_user.id)


def _insert_category(name: str) -> int:
    conn = conn_mod.get_connection()
    try:
        cur = conn.execute('INSERT INTO "Category"(Name) VALUES (?)', (name,))
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


@pytest.mark.integration
def test_admin_sets_item_categories_and_catalog_filter_returns_matching_items(app):
    admin_id = _make_admin(app)

    furniture_id = _insert_category("Furniture")
    office_id = _insert_category("Office")
    lighting_id = _insert_category("Lighting")

    # Create item with categories Furniture + Office
    created = app.ui_admin_create_item(
        admin_user_id=admin_id,
        name="Office Desk",
        description="Desk",
        price=300.0,
        weight=25.0,
        length=120.0,   # depth in DB
        width=60.0,
        height=75.0,
        pictures=[],
        category_ids=[furniture_id, office_id],
    )
    assert created.ok, created.error.message
    desk_item_id = int(created.data)

    # Filter by Lighting -> should NOT contain desk
    f1 = app.ui_list_items_filtered(display_currency="EUR", category_ids=[lighting_id])
    assert f1.ok, f1.error.message
    ids1 = [int(x["id"]) for x in (f1.data or [])]
    assert desk_item_id not in ids1

    # Filter by Office -> should contain desk
    f2 = app.ui_list_items_filtered(display_currency="EUR", category_ids=[office_id])
    assert f2.ok
    ids2 = [int(x["id"]) for x in (f2.data or [])]
    assert desk_item_id in ids2

    # Update categories to only Lighting
    upd = app.ui_admin_update_item(
        item_id=desk_item_id,
        name="Office Desk",
        description="Desk",
        price=300.0,
        weight=25.0,
        length=120.0,
        width=60.0,
        height=75.0,
        pictures=[],
        category_ids=[lighting_id],
    )
    assert upd.ok, upd.error.message

    # Now: Office filter should not contain it, Lighting should contain it
    f3 = app.ui_list_items_filtered(display_currency="EUR", category_ids=[office_id])
    assert f3.ok
    ids3 = [int(x["id"]) for x in (f3.data or [])]
    assert desk_item_id not in ids3

    f4 = app.ui_list_items_filtered(display_currency="EUR", category_ids=[lighting_id])
    assert f4.ok
    ids4 = [int(x["id"]) for x in (f4.data or [])]
    assert desk_item_id in ids4
