import pytest

import app.db.connection as conn_mod
from app.db import schema, seed
from app.services.store_app_service import StoreAppService


@pytest.mark.integration
def test_favorites_flow_add_list_remove(tmp_path, monkeypatch):
    # --- Temporary DB ---
    data_dir = tmp_path / "data"
    db_path = data_dir / "omnistore.db"
    monkeypatch.setattr(conn_mod, "DATA_DIR", data_dir, raising=False)
    monkeypatch.setattr(conn_mod, "DB_PATH", db_path, raising=False)

    schema.init_db()
    seed.seed_demo_data_if_empty()

    app = StoreAppService.create_default()

    # Resolve customer id by seed email
    customer = app.user_repo.get_by_email("customer@omnistore.local")
    assert customer is not None
    customer_id = int(customer.id)

    # Pick an existing item id from catalog
    items_res = app.ui_list_items(display_currency="EUR")
    assert items_res.ok is True
    items = items_res.data
    assert len(items) > 0
    item_id = int(items[0]["id"])

    # 1) Add favorite
    add_res = app.ui_add_favorite(customer_id, item_id)
    assert add_res.ok is True

    # 2) List favorites -> should contain item
    list_res = app.ui_list_favorites(customer_id)
    assert list_res.ok is True
    favs = list_res.data
    assert any(int(x["id"]) == item_id for x in favs)

    # 3) Remove favorite
    rem_res = app.ui_remove_favorite(customer_id, item_id)
    assert rem_res.ok is True

    # 4) List again -> should NOT contain item
    list_res2 = app.ui_list_favorites(customer_id)
    assert list_res2.ok is True
    favs2 = list_res2.data
    assert all(int(x["id"]) != item_id for x in favs2)
