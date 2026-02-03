import pytest

import app.db.connection as conn_mod
from app.db import schema, seed
from app.services.store_app_service import StoreAppService


@pytest.mark.integration
def test_admin_crud_create_update_delete_with_categories(tmp_path, monkeypatch):
    # --- Temporary DB ---
    data_dir = tmp_path / "data"
    db_path = data_dir / "omnistore.db"
    monkeypatch.setattr(conn_mod, "DATA_DIR", data_dir, raising=False)
    monkeypatch.setattr(conn_mod, "DB_PATH", db_path, raising=False)

    schema.init_db()
    seed.seed_demo_data_if_empty()

    app = StoreAppService.create_default()

    # Resolve admin id from seed email
    admin = app.user_repo.get_by_email("admin@omnistore.local")
    assert admin is not None
    admin_id = int(admin.id)

    # Load categories to attach to item
    cats_res = app.ui_admin_list_categories()
    assert cats_res.ok is True
    cats = cats_res.data
    assert len(cats) >= 2
    c1 = int(cats[0]["id"])
    c2 = int(cats[1]["id"])

    # 1) CREATE item with categories
    create_res = app.ui_admin_create_item(
        admin_user_id=admin_id,
        name="Integration Test Item",
        description="Created by integration test",
        price=99.99,
        weight=1.5,
        length=10.0,   # Depth in DB
        width=20.0,
        height=30.0,
        pictures=[],
        category_ids=[c1, c2],
    )
    assert create_res.ok is True
    new_id = int(create_res.data)

    # 2) GET -> should contain category_ids
    get_res = app.ui_admin_get_item(new_id)
    assert get_res.ok is True
    item = get_res.data
    assert int(item["id"]) == new_id
    assert item["name"] == "Integration Test Item"
    assert set(int(x) for x in item.get("category_ids", [])) == {c1, c2}

    # 3) UPDATE -> change name + categories (keep only c1)
    upd_res = app.ui_admin_update_item(
        item_id=new_id,
        name="Integration Test Item (Updated)",
        description="Updated by integration test",
        price=120.00,
        weight=2.0,
        length=11.0,
        width=21.0,
        height=31.0,
        pictures=[],
        category_ids=[c1],
    )
    assert upd_res.ok is True

    get2_res = app.ui_admin_get_item(new_id)
    assert get2_res.ok is True
    item2 = get2_res.data
    assert item2["name"] == "Integration Test Item (Updated)"
    assert set(int(x) for x in item2.get("category_ids", [])) == {c1}

    # 4) DELETE
    del_res = app.ui_admin_delete_item(new_id)
    assert del_res.ok is True

    # 5) GET after delete -> should fail
    get3_res = app.ui_admin_get_item(new_id)
    assert get3_res.ok is False
