from app.db.connection import get_connection, execute_script


SCHEMA_SQL = """
-- USERS
CREATE TABLE IF NOT EXISTS User (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Username TEXT NOT NULL UNIQUE,
    Password TEXT NOT NULL,
    Name TEXT NOT NULL,
    Email TEXT NOT NULL UNIQUE
);

-- ADMIN (1:1 към User)
CREATE TABLE IF NOT EXISTS Admin (
    UserID INTEGER PRIMARY KEY,
    Role TEXT NOT NULL,
    FOREIGN KEY(UserID) REFERENCES User(ID) ON DELETE CASCADE
);

-- CUSTOMER (1:1 към User)
CREATE TABLE IF NOT EXISTS Customer (
    UserID INTEGER PRIMARY KEY,
    Currency TEXT NOT NULL,
    FOREIGN KEY(UserID) REFERENCES User(ID) ON DELETE CASCADE
);

-- CATEGORY
CREATE TABLE IF NOT EXISTS Category (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name TEXT NOT NULL UNIQUE
);

-- ITEM
CREATE TABLE IF NOT EXISTS Item (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    AdminUserID INTEGER NOT NULL,
    Name TEXT NOT NULL,
    Description TEXT NOT NULL,
    Height REAL NOT NULL,
    Width REAL NOT NULL,
    Depth REAL NOT NULL,
    Weight REAL NOT NULL,
    Price REAL NOT NULL,
    FOREIGN KEY(AdminUserID) REFERENCES Admin(UserID) ON DELETE RESTRICT
);

-- ITEM_CATEGORY (many-to-many)
CREATE TABLE IF NOT EXISTS Item_Category (
    ItemID INTEGER NOT NULL,
    CategoryID INTEGER NOT NULL,
    PRIMARY KEY(ItemID, CategoryID),
    FOREIGN KEY(ItemID) REFERENCES Item(ID) ON DELETE CASCADE,
    FOREIGN KEY(CategoryID) REFERENCES Category(ID) ON DELETE CASCADE
);

-- PICTURE (1:N към Item)
CREATE TABLE IF NOT EXISTS Picture (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    ItemID INTEGER NOT NULL,
    FilePath TEXT NOT NULL,
    IsMain INTEGER NOT NULL DEFAULT 0, -- 0/1
    FOREIGN KEY(ItemID) REFERENCES Item(ID) ON DELETE CASCADE
);

-- CART (1:1 към Customer в твоята диаграма: CustomerUserID е UNIQUE)
CREATE TABLE IF NOT EXISTS Cart (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerUserID INTEGER NOT NULL UNIQUE,
    FOREIGN KEY(CustomerUserID) REFERENCES Customer(UserID) ON DELETE CASCADE
);

-- ITEM_CART (cart items)
CREATE TABLE IF NOT EXISTS Item_Cart (
    CartID INTEGER NOT NULL,
    ItemID INTEGER NOT NULL,
    Quantity INTEGER NOT NULL,
    PRIMARY KEY(CartID, ItemID),
    FOREIGN KEY(CartID) REFERENCES Cart(ID) ON DELETE CASCADE,
    FOREIGN KEY(ItemID) REFERENCES Item(ID) ON DELETE CASCADE
);

-- FAVORITES (Customer <-> Item)
CREATE TABLE IF NOT EXISTS Favorites (
    CustomerUserID INTEGER NOT NULL,
    ItemID INTEGER NOT NULL,
    PRIMARY KEY(CustomerUserID, ItemID),
    FOREIGN KEY(CustomerUserID) REFERENCES Customer(UserID) ON DELETE CASCADE,
    FOREIGN KEY(ItemID) REFERENCES Item(ID) ON DELETE CASCADE
);

-- HISTORY (Customer <-> Item + timestamp)
CREATE TABLE IF NOT EXISTS History (
    CustomerUserID INTEGER NOT NULL,
    ItemID INTEGER NOT NULL,
    ViewedAt TEXT NOT NULL, -- ISO timestamp string
    PRIMARY KEY(CustomerUserID, ItemID, ViewedAt),
    FOREIGN KEY(CustomerUserID) REFERENCES Customer(UserID) ON DELETE CASCADE,
    FOREIGN KEY(ItemID) REFERENCES Item(ID) ON DELETE CASCADE
);

-- Orders (Checkout)
CREATE TABLE IF NOT EXISTS "Order" (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    CustomerUserID INTEGER NOT NULL,
    CreatedAt TEXT NOT NULL,
    Status TEXT NOT NULL DEFAULT 'CREATED',
    TotalBase REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (CustomerUserID) REFERENCES Customer(UserID) ON DELETE RESTRICT,
    CHECK (Status IN ('CREATED', 'PAID', 'CANCELLED'))
);

CREATE TABLE IF NOT EXISTS OrderItem (
    OrderID INTEGER NOT NULL,
    ItemID INTEGER NULL,
    ItemName TEXT NOT NULL,
    UnitPriceBase REAL NOT NULL,
    Quantity INTEGER NOT NULL,
    PRIMARY KEY (OrderID, ItemID),
    FOREIGN KEY (OrderID) REFERENCES "Order"(ID) ON DELETE CASCADE,
    FOREIGN KEY (ItemID) REFERENCES Item(ID) ON DELETE SET NULL,
    CHECK (Quantity > 0)
);

-- Helpful indexes (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_item_admin ON Item(AdminUserID);
CREATE INDEX IF NOT EXISTS idx_picture_item ON Picture(ItemID);
CREATE INDEX IF NOT EXISTS idx_item_category_cat ON Item_Category(CategoryID);
CREATE INDEX IF NOT EXISTS idx_item_cart_item ON Item_Cart(ItemID);
CREATE INDEX IF NOT EXISTS idx_fav_item ON Favorites(ItemID);
CREATE INDEX IF NOT EXISTS idx_hist_item ON History(ItemID);
CREATE INDEX IF NOT EXISTS idx_order_customer ON "Order"(CustomerUserID);
CREATE INDEX IF NOT EXISTS idx_order_created ON "Order"(CreatedAt);
CREATE INDEX IF NOT EXISTS idx_orderitem_order ON OrderItem(OrderID);
"""


def init_db() -> None:
    conn = get_connection()
    try:
        execute_script(conn, SCHEMA_SQL)
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Database schema initialized.")
