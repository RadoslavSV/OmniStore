from __future__ import annotations

from app.db.connection import get_connection


def seed_demo_data_if_empty() -> None:
    """
    Seeds demo data ONLY if Item table is empty.

    - Users are created via StoreAppService.ui_register_* so password hashing + validations match the app.
    - Items/categories/pictures are inserted via direct SQL to avoid repository API mismatches.
    """
    conn = get_connection()
    try:
        # If items already exist -> do nothing
        if conn.execute('SELECT 1 FROM "Item" LIMIT 1').fetchone():
            return
    finally:
        conn.close()

    # --- 1) Create demo users through the app facade (correct hashing)
    admin_user_id = _ensure_admin_user()
    customer_user_id = _ensure_customer_user()

    # --- 2) Seed catalog data via SQL (stable with schema)
    conn = get_connection()
    try:
        # Categories
        furniture_id = _ensure_category(conn, "Furniture")
        office_id = _ensure_category(conn, "Office")
        lighting_id = _ensure_category(conn, "Lighting")

        # Items (require Admin FK)
        desk_id = _insert_item(
            conn,
            admin_user_id=admin_user_id,
            name="Office Desk",
            description="Wooden office desk with drawers",
            height=75.0,
            width=60.0,
            depth=120.0,
            weight=25.5,
            price=300.0,
        )
        lamp_id = _insert_item(
            conn,
            admin_user_id=admin_user_id,
            name="Desk Lamp",
            description="LED desk lamp with adjustable arm",
            height=45.0,
            width=18.0,
            depth=18.0,
            weight=1.2,
            price=40.0,
        )
        chair_id = _insert_item(
            conn,
            admin_user_id=admin_user_id,
            name="Office Chair",
            description="Ergonomic chair with lumbar support",
            height=110.0,
            width=65.0,
            depth=65.0,
            weight=12.0,
            price=180.0,
        )

        # Item_Category links
        _link_item_category(conn, desk_id, furniture_id)
        _link_item_category(conn, desk_id, office_id)

        _link_item_category(conn, lamp_id, lighting_id)
        _link_item_category(conn, lamp_id, office_id)

        _link_item_category(conn, chair_id, office_id)

        # Pictures (placeholder paths)
        _insert_picture(conn, desk_id, r"images\desk_1.png", is_main=True)
        _insert_picture(conn, desk_id, r"images\desk_2.png", is_main=False)
        _insert_picture(conn, lamp_id, r"images\lamp_1.png", is_main=True)
        _insert_picture(conn, chair_id, r"images\chair_1.png", is_main=True)

        conn.commit()
    finally:
        conn.close()


# ---------- Demo users via StoreAppService (correct password hashing) ----------

def _ensure_admin_user() -> int:
    from app.services.store_app_service import StoreAppService
    from app.db.connection import get_connection

    app = StoreAppService.create_default()

    # Check if user exists
    user = app.user_repo.get_by_email("admin@omnistore.local")
    if not user:
        r = app.ui_register_customer(
            username="admin",
            email="admin@omnistore.local",
            name="Demo Admin",
            password="admin123",
            currency="EUR",
        )
        if not r.ok:
            raise RuntimeError(f"Seed admin register failed: {r.error.message}")
        user = r.data

    user_id = int(user.id)

    # Ensure Admin row exists via SQL (no repo method assumptions)
    conn = get_connection()
    try:
        row = conn.execute('SELECT UserID FROM "Admin" WHERE UserID = ?', (user_id,)).fetchone()
        if not row:
            conn.execute('INSERT INTO "Admin"(UserID, Role) VALUES (?, ?)', (user_id, "ADMIN"))
            conn.commit()
    finally:
        conn.close()

    return user_id

def _ensure_customer_user() -> int:
    from app.services.store_app_service import StoreAppService
    from app.db.connection import get_connection

    app = StoreAppService.create_default()

    user = app.user_repo.get_by_email("customer@omnistore.local")
    if not user:
        r = app.ui_register_customer(
            username="customer",
            email="customer@omnistore.local",
            name="Demo Customer",
            password="customer123",
            currency="EUR",
        )
        if not r.ok:
            raise RuntimeError(f"Seed customer register failed: {r.error.message}")
        user = r.data

    user_id = int(user.id)

    # Ensure Customer row exists + Cart via SQL
    conn = get_connection()
    try:
        row = conn.execute('SELECT UserID FROM "Customer" WHERE UserID = ?', (user_id,)).fetchone()
        if not row:
            conn.execute('INSERT INTO "Customer"(UserID, Currency) VALUES (?, ?)', (user_id, "EUR"))

        row = conn.execute('SELECT ID FROM "Cart" WHERE CustomerUserID = ?', (user_id,)).fetchone()
        if not row:
            conn.execute('INSERT INTO "Cart"(CustomerUserID) VALUES (?)', (user_id,))

        conn.commit()
    finally:
        conn.close()

    return user_id


# ---------- Direct SQL helpers (stable with schema) ----------

def _ensure_category(conn, name: str) -> int:
    row = conn.execute('SELECT ID FROM "Category" WHERE Name = ?', (name,)).fetchone()
    if row:
        return int(row["ID"])
    cur = conn.execute('INSERT INTO "Category"(Name) VALUES (?)', (name,))
    return int(cur.lastrowid)


def _insert_item(
    conn,
    *,
    admin_user_id: int,
    name: str,
    description: str,
    height: float,
    width: float,
    depth: float,
    weight: float,
    price: float,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO "Item"(AdminUserID, Name, Description, Height, Width, Depth, Weight, Price)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (admin_user_id, name, description, height, width, depth, weight, price),
    )
    return int(cur.lastrowid)


def _link_item_category(conn, item_id: int, category_id: int) -> None:
    conn.execute(
        'INSERT OR IGNORE INTO "Item_Category"(ItemID, CategoryID) VALUES (?, ?)',
        (item_id, category_id),
    )


def _insert_picture(conn, item_id: int, file_path: str, *, is_main: bool) -> None:
    conn.execute(
        'INSERT INTO "Picture"(ItemID, FilePath, IsMain) VALUES (?, ?, ?)',
        (item_id, file_path, 1 if is_main else 0),
    )
