import pytest

import app.db.connection as conn_mod
from app.db import schema, seed
from app.services.store_app_service import StoreAppService


@pytest.mark.integration
def test_history_flow_record_list_clear(tmp_path, monkeypatch):
    # --- Temporary DB ---
    data_dir = tmp_path / "data"
    db_path = data_dir / "omnistore.db"
    monkeypatch.setattr(conn_mod, "DATA_DIR", data_dir, raising=False)
    monkeypatch.setattr(conn_mod, "DB_PATH", db_path, raising=False)

    schema.init_db()
    seed.seed_demo_data_if_empty()

    app = StoreAppService.create_default()

    # Resolve customer id
    customer = app.user_repo.get_by_email("customer@omnistore.local")
    assert customer is not None
    customer_id = int(customer.id)

    # Choose an item
    items_res = app.ui_list_items(display_currency="EUR")
    assert items_res.ok is True
    items = items_res.data
    assert len(items) > 0
    item_id = int(items[0]["id"])

    # 1) Record a view (facade -> SQL)
    rec = app.ui_record_view(customer_id, item_id)
    assert rec.ok is True

    # 2) List history -> should include item_id
    hist = app.ui_list_history(customer_id, limit=50)
    assert hist.ok is True
    rows = hist.data
    assert any(int(r["item_id"]) == item_id for r in rows)

    # 3) Clear history via HistoryService (service -> repo -> DB)
    app.history.clear_history(customer_id)

    # 4) List again -> should be empty (or at least not include the item)
    hist2 = app.ui_list_history(customer_id, limit=50)
    assert hist2.ok is True
    rows2 = hist2.data
    assert all(int(r["item_id"]) != item_id for r in rows2)
