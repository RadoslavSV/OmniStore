import pytest

import app.db.connection as conn_mod
from app.db import schema, seed
from app.services.store_app_service import StoreAppService


@pytest.mark.integration
def test_catalog_category_filter_returns_only_items_in_selected_categories(tmp_path, monkeypatch):
    # --- Redirect DB to a temporary file (isolated integration DB) ---
    data_dir = tmp_path / "data"
    db_path = data_dir / "omnistore.db"
    monkeypatch.setattr(conn_mod, "DATA_DIR", data_dir, raising=False)
    monkeypatch.setattr(conn_mod, "DB_PATH", db_path, raising=False)

    schema.init_db()
    seed.seed_demo_data_if_empty()

    app = StoreAppService.create_default()

    # 1) Load categories
    rcat = app.ui_list_categories()
    assert rcat.ok is True
    categories = rcat.data
    assert isinstance(categories, list)
    assert len(categories) > 0

    # choose 1 category id
    chosen = categories[0]["id"]

    # 2) Get filtered items (ANY match)
    ritems = app.ui_list_items_filtered(display_currency="EUR", category_ids=[chosen])
    assert ritems.ok is True
    items = ritems.data
    assert isinstance(items, list)

    # 3) Verify that each returned item is linked to chosen category in DB
    conn = conn_mod.get_connection()
    try:
        for it in items:
            item_id = int(it["id"])
            row = conn.execute(
                """
                SELECT 1
                FROM "Item_Category"
                WHERE ItemID = ? AND CategoryID = ?
                LIMIT 1
                """,
                (item_id, int(chosen)),
            ).fetchone()
            assert row is not None, f"Item {item_id} is not linked to category {chosen}"
    finally:
        conn.close()
