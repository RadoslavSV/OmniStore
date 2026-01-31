from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict

from datetime import datetime, timezone

from app.models.user import User

from app.repositories.user_repository import UserRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.customer_repository import CustomerRepository

from app.repositories.item_repository import ItemRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.item_category_repository import ItemCategoryRepository
from app.repositories.picture_repository import PictureRepository

from app.repositories.cart_repository import CartRepository
from app.repositories.item_cart_repository import ItemCartRepository

from app.repositories.favorites_repository import FavoritesRepository
from app.repositories.history_repository import HistoryRepository

from app.repositories.order_repository import OrderRepository
from app.repositories.order_item_repository import OrderItemRepository

from app.services.auth_service import AuthService
from app.services.role_service import RoleService
from app.services.cart_service import CartService
from app.services.checkout_service import CheckoutService
from app.services.order_history_service import OrderHistoryService
from app.services.favorites_service import FavoritesService
from app.services.history_service import HistoryService

from app.services.currency_service import CurrencyService

from app.presentation.app_result import AppResult
from app.presentation.error_mapper import map_exception
from app.presentation.app_exceptions import AppError
from app.presentation.dto import (
    item_list_dto,
    item_details_dto,
    cart_dto,
    order_list_dto,
    order_details_dto,
)

from app.db.connection import get_connection


@dataclass
class StoreAppService:
    """
    Facade used by UI layer.
    UI should talk ONLY to this service (no direct repository access).

    Notes:
    - Prices in DB are base currency EUR.
    - CurrencyService controlled by env (you set OMNISTORE_ENABLE_CURRENCY_API=1).
    """

    # Repos
    user_repo: UserRepository
    admin_repo: AdminRepository
    customer_repo: CustomerRepository

    item_repo: ItemRepository
    category_repo: CategoryRepository
    item_category_repo: ItemCategoryRepository
    picture_repo: PictureRepository

    cart_repo: CartRepository
    item_cart_repo: ItemCartRepository

    favorites_repo: FavoritesRepository
    history_repo: HistoryRepository

    order_repo: OrderRepository
    order_item_repo: OrderItemRepository

    # Services
    auth: AuthService
    roles: RoleService
    cart: CartService
    checkout: CheckoutService
    order_history: OrderHistoryService
    favorites: FavoritesService
    history: HistoryService

    # Currency
    currency: CurrencyService

    base_currency: str = "EUR"

    # ---------- Factory ----------

    @classmethod
    def create_default(cls) -> "StoreAppService":
        user_repo = UserRepository()
        admin_repo = AdminRepository()
        customer_repo = CustomerRepository()

        item_repo = ItemRepository()
        category_repo = CategoryRepository()
        item_category_repo = ItemCategoryRepository()
        picture_repo = PictureRepository()

        cart_repo = CartRepository()
        item_cart_repo = ItemCartRepository()

        favorites_repo = FavoritesRepository()
        history_repo = HistoryRepository()

        order_repo = OrderRepository()
        order_item_repo = OrderItemRepository()

        auth = AuthService(user_repo)
        roles = RoleService(admin_repo, customer_repo)

        currency = CurrencyService()

        cart = CartService(
            cart_repo=cart_repo,
            item_cart_repo=item_cart_repo,
            item_repo=item_repo,
            customer_repo=customer_repo,
            base_currency="EUR",
        )

        checkout = CheckoutService(
            cart_repo=cart_repo,
            item_cart_repo=item_cart_repo,
            item_repo=item_repo,
            order_repo=order_repo,
            order_item_repo=order_item_repo,
            base_currency="EUR",
        )

        order_history = OrderHistoryService(order_repo, order_item_repo)

        favorites = FavoritesService(favorites_repo, item_repo)
        history = HistoryService(history_repo, item_repo)

        return cls(
            user_repo=user_repo,
            admin_repo=admin_repo,
            customer_repo=customer_repo,
            item_repo=item_repo,
            category_repo=category_repo,
            item_category_repo=item_category_repo,
            picture_repo=picture_repo,
            cart_repo=cart_repo,
            item_cart_repo=item_cart_repo,
            favorites_repo=favorites_repo,
            history_repo=history_repo,
            order_repo=order_repo,
            order_item_repo=order_item_repo,
            auth=auth,
            roles=roles,
            cart=cart,
            checkout=checkout,
            order_history=order_history,
            favorites=favorites,
            history=history,
            currency=currency,
            base_currency="EUR",
        )

    # ---------- Auth / Roles ----------

    def register_customer(self, username: str, email: str, name: str, password: str, currency: str = "EUR") -> User:
        user = self.auth.register(username=username, email=email, name=name, password=password)
        self.roles.make_customer(user.id, currency=(currency or self.base_currency).upper())
        return self.roles.enrich_user_role(user)

    def login(self, email: str, password: str) -> User:
        user = self.auth.login(email=email, password=password)
        return self.roles.enrich_user_role(user)

    def ensure_admin(self, user_id: int) -> None:
        self.roles.make_admin(user_id)

    # ---------- Currency prefs ----------

    def set_customer_currency(self, user_id: int, currency: str) -> None:
        currency = (currency or self.base_currency).upper()
        self.customer_repo.set_currency(user_id, currency)

    def get_customer_currency(self, user_id: int) -> str:
        return (self.customer_repo.get_currency(user_id) or self.base_currency).upper()

    def list_supported_currencies(self) -> List[str]:
        try:
            lst = self.currency.list_supported_currencies() or []
        except Exception:
            lst = []
        baseline = ["EUR", "USD", "GBP", "BGN", "RON", "TRY", "CHF", "JPY", "CAD", "AUD"]
        out = set([c.upper() for c in baseline])
        for c in lst:
            if c:
                out.add(str(c).upper())
        return sorted(out)

    # ---------- Catalog ----------

    def list_items(self, display_currency: Optional[str] = None) -> List[Dict]:
        items = self.item_repo.list_all() or []
        target = (display_currency or self.base_currency).upper()

        out: List[Dict] = []
        for it in items:
            price_base = float(it.price)
            price = price_base
            if target != self.base_currency:
                price = self.currency.convert(price_base, to_currency=target, from_currency=self.base_currency)

            out.append(
                {
                    "item_id": it.id,
                    "name": it.name,
                    "price_base": price_base,
                    "price": float(price),
                    "currency": target,
                }
            )
        return out

    def get_item_details(self, item_id: int) -> dict:
        item = self.item_repo.get_by_id(item_id)
        if not item:
            raise AppError("Item not found")

        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT c.Name AS Name
                FROM "Item_Category" ic
                JOIN "Category" c ON c.ID = ic.CategoryID
                WHERE ic.ItemID = ?
                ORDER BY c.Name ASC
                """,
                (int(item_id),),
            )
            categories = [r["Name"] for r in cur.fetchall()]

            cur = conn.execute(
                """
                SELECT FilePath, IsMain
                FROM "Picture"
                WHERE ItemID = ?
                ORDER BY IsMain DESC, ID ASC
                """,
                (int(item_id),),
            )
            pics = cur.fetchall()
        finally:
            conn.close()

        pictures = [p["FilePath"] for p in pics] if pics else []
        main_pic = None
        for p in pics:
            if int(p["IsMain"]) == 1:
                main_pic = p["FilePath"]
                break
        if main_pic is None and pictures:
            main_pic = pictures[0]

        return {"item": item, "categories": categories, "pictures": pictures, "main_picture": main_pic}

    # ---------- Cart ----------

    def add_to_cart(self, customer_user_id: int, item_id: int, quantity: int = 1) -> None:
        self.cart.add_item(customer_user_id, item_id, quantity)

    def set_cart_quantity(self, customer_user_id: int, item_id: int, quantity: int) -> None:
        self.cart.set_quantity(customer_user_id, item_id, quantity)

    def remove_from_cart(self, customer_user_id: int, item_id: int) -> None:
        self.cart.remove_item(customer_user_id, item_id)

    def get_cart(self, customer_user_id: int, display_currency: Optional[str] = None) -> Dict:
        items = self.cart.get_detailed_items(customer_user_id, display_currency=display_currency)
        total = self.cart.get_total(customer_user_id, display_currency=display_currency)
        return {"items": items, "total": total}

    # ---------- Checkout / Orders ----------

    def proceed_to_checkout(self, customer_user_id: int) -> int:
        return self.checkout.checkout(customer_user_id)

    def list_orders(self, customer_user_id: int, limit: int = 50) -> List[Dict]:
        return self.order_history.list_orders(customer_user_id, limit=limit)

    def get_order_details(self, customer_user_id: int, order_id: int) -> Dict:
        return self.order_history.get_order_details(customer_user_id, order_id)

    # ============================================================
    # ADMIN: Manage Items (CRUD via direct SQL)
    # - Supports dimensions + pictures.
    # - Robust to schema differences (detects columns via PRAGMA).
    # ============================================================

    @staticmethod
    def _table_exists(conn, name: str) -> bool:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name = ? COLLATE NOCASE",
            (name,),
        ).fetchone()
        return row is not None

    @staticmethod
    def _item_columns(conn) -> set[str]:
        cols = set()
        try:
            for r in conn.execute('PRAGMA table_info("Item")').fetchall():
                cols.add(str(r["name"]))
        except Exception:
            # fallback: maybe unquoted
            for r in conn.execute("PRAGMA table_info(Item)").fetchall():
                cols.add(str(r["name"]))
        return cols

    def _pictures_for_item(self, conn, item_id: int) -> list[str]:
        if not self._table_exists(conn, "Picture"):
            return []
        try:
            rows = conn.execute(
                'SELECT FilePath FROM "Picture" WHERE ItemID = ? ORDER BY IsMain DESC, ID ASC',
                (int(item_id),),
            ).fetchall()
            return [r["FilePath"] for r in rows] if rows else []
        except Exception:
            return []

    def _replace_pictures(self, conn, item_id: int, pictures: list[str]) -> None:
        if not self._table_exists(conn, "Picture"):
            return

        # normalize -> store as images/<filename> if it's not already a path
        norm: list[str] = []
        for p in pictures or []:
            p = str(p).strip()
            if not p:
                continue
            if "/" in p or "\\" in p:
                # if someone passes a path, normalize to forward slashes
                p = p.replace("\\", "/")
                norm.append(p)
            else:
                norm.append(f"images/{p}")

        # clear existing
        conn.execute('DELETE FROM "Picture" WHERE ItemID = ?', (int(item_id),))

        # insert new (first = main)
        for idx, fp in enumerate(norm):
            is_main = 1 if idx == 0 else 0
            conn.execute(
                'INSERT INTO "Picture"(ItemID, FilePath, IsMain) VALUES (?, ?, ?)',
                (int(item_id), fp, int(is_main)),
            )

    def admin_list_items(self) -> List[Dict]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ID, Name, Price, COALESCE(Weight, 0) as Weight
                FROM "Item"
                ORDER BY ID ASC
                """
            )
            return [
                {
                    "id": int(r["ID"]),
                    "name": r["Name"],
                    "price": float(r["Price"]),
                    "weight": float(r["Weight"]),
                    "currency": "EUR",
                }
                for r in cur.fetchall()
            ]
        finally:
            conn.close()

    def admin_get_item(self, item_id: int) -> Dict:
        conn = get_connection()
        try:
            cols = self._item_columns(conn)
            pictures = self._pictures_for_item(conn, item_id)

            # --- Case 1: dimensions stored directly on Item table ---
            if {"Length", "Width", "Height"}.issubset(cols):
                r = conn.execute(
                    """
                    SELECT ID, Name, COALESCE(Description,'') as Description,
                           Price, COALESCE(Weight,0) as Weight,
                           COALESCE(Length,0) as Length, COALESCE(Width,0) as Width, COALESCE(Height,0) as Height
                    FROM "Item"
                    WHERE ID = ?
                    """,
                    (int(item_id),),
                ).fetchone()
                if not r:
                    raise AppError("Item not found")

                return {
                    "id": int(r["ID"]),
                    "name": r["Name"],
                    "description": r["Description"] or "",
                    "price": float(r["Price"]),
                    "weight": float(r["Weight"]),
                    "length": float(r["Length"]),
                    "width": float(r["Width"]),
                    "height": float(r["Height"]),
                    "pictures": pictures,
                    "currency": "EUR",
                }

            # --- Case 2: DimensionsID pattern (Dimensions table) ---
            if "DimensionsID" in cols and self._table_exists(conn, "Dimensions"):
                r = conn.execute(
                    """
                    SELECT i.ID, i.Name, COALESCE(i.Description,'') as Description,
                           i.Price, COALESCE(i.Weight,0) as Weight,
                           COALESCE(d.Length,0) as Length, COALESCE(d.Width,0) as Width, COALESCE(d.Height,0) as Height
                    FROM "Item" i
                    LEFT JOIN "Dimensions" d ON d.ID = i.DimensionsID
                    WHERE i.ID = ?
                    """,
                    (int(item_id),),
                ).fetchone()
                if not r:
                    raise AppError("Item not found")

                return {
                    "id": int(r["ID"]),
                    "name": r["Name"],
                    "description": r["Description"] or "",
                    "price": float(r["Price"]),
                    "weight": float(r["Weight"]),
                    "length": float(r["Length"]),
                    "width": float(r["Width"]),
                    "height": float(r["Height"]),
                    "pictures": pictures,
                    "currency": "EUR",
                }

            # --- Fallback: no dimensions columns known ---
            r = conn.execute(
                """
                SELECT ID, Name, COALESCE(Description,'') as Description, Price, COALESCE(Weight,0) as Weight
                FROM "Item"
                WHERE ID = ?
                """,
                (int(item_id),),
            ).fetchone()
            if not r:
                raise AppError("Item not found")

            return {
                "id": int(r["ID"]),
                "name": r["Name"],
                "description": r["Description"] or "",
                "price": float(r["Price"]),
                "weight": float(r["Weight"]),
                "length": 0.0,
                "width": 0.0,
                "height": 0.0,
                "pictures": pictures,
                "currency": "EUR",
            }
        finally:
            conn.close()

    def admin_create_item(
        self,
        *,
        name: str,
        description: str,
        price: float,
        weight: float,
        length: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        pictures: Optional[List[str]] = None,
    ) -> int:
        conn = get_connection()
        try:
            cols = self._item_columns(conn)

            # 1) Insert item (schema-aware)
            if {"Length", "Width", "Height"}.issubset(cols):
                cur = conn.execute(
                    """
                    INSERT INTO "Item"(Name, Description, Price, Weight, Length, Width, Height)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (name, description, float(price), float(weight), float(length), float(width), float(height)),
                )
                item_id = int(cur.lastrowid)

            elif "DimensionsID" in cols and self._table_exists(conn, "Dimensions"):
                # create dimensions row first
                dcur = conn.execute(
                    """
                    INSERT INTO "Dimensions"(Length, Width, Height)
                    VALUES (?, ?, ?)
                    """,
                    (float(length), float(width), float(height)),
                )
                dim_id = int(dcur.lastrowid)

                cur = conn.execute(
                    """
                    INSERT INTO "Item"(Name, Description, Price, Weight, DimensionsID)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (name, description, float(price), float(weight), int(dim_id)),
                )
                item_id = int(cur.lastrowid)

            else:
                # bare minimum insert (if your schema allows it)
                cur = conn.execute(
                    """
                    INSERT INTO "Item"(Name, Description, Price, Weight)
                    VALUES (?, ?, ?, ?)
                    """,
                    (name, description, float(price), float(weight)),
                )
                item_id = int(cur.lastrowid)

            # 2) Pictures
            if pictures is None:
                pictures = []
            self._replace_pictures(conn, item_id, pictures)

            conn.commit()
            return item_id
        finally:
            conn.close()

    def admin_update_item(
        self,
        *,
        item_id: int,
        name: str,
        description: str,
        price: float,
        weight: float,
        length: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        pictures: Optional[List[str]] = None,
    ) -> None:
        conn = get_connection()
        try:
            cols = self._item_columns(conn)

            if {"Length", "Width", "Height"}.issubset(cols):
                cur = conn.execute(
                    """
                    UPDATE "Item"
                    SET Name = ?, Description = ?, Price = ?, Weight = ?, Length = ?, Width = ?, Height = ?
                    WHERE ID = ?
                    """,
                    (name, description, float(price), float(weight), float(length), float(width), float(height), int(item_id)),
                )
                if cur.rowcount == 0:
                    raise AppError("Item not found")

            elif "DimensionsID" in cols and self._table_exists(conn, "Dimensions"):
                # fetch DimensionsID
                row = conn.execute('SELECT DimensionsID FROM "Item" WHERE ID = ?', (int(item_id),)).fetchone()
                if not row:
                    raise AppError("Item not found")
                dim_id = row["DimensionsID"]

                # update item
                conn.execute(
                    """
                    UPDATE "Item"
                    SET Name = ?, Description = ?, Price = ?, Weight = ?
                    WHERE ID = ?
                    """,
                    (name, description, float(price), float(weight), int(item_id)),
                )

                # update dimensions (create if missing)
                if dim_id:
                    conn.execute(
                        """
                        UPDATE "Dimensions"
                        SET Length = ?, Width = ?, Height = ?
                        WHERE ID = ?
                        """,
                        (float(length), float(width), float(height), int(dim_id)),
                    )
                else:
                    dcur = conn.execute(
                        """
                        INSERT INTO "Dimensions"(Length, Width, Height)
                        VALUES (?, ?, ?)
                        """,
                        (float(length), float(width), float(height)),
                    )
                    new_dim_id = int(dcur.lastrowid)
                    conn.execute('UPDATE "Item" SET DimensionsID = ? WHERE ID = ?', (int(new_dim_id), int(item_id)))

            else:
                cur = conn.execute(
                    """
                    UPDATE "Item"
                    SET Name = ?, Description = ?, Price = ?, Weight = ?
                    WHERE ID = ?
                    """,
                    (name, description, float(price), float(weight), int(item_id)),
                )
                if cur.rowcount == 0:
                    raise AppError("Item not found")

            if pictures is None:
                pictures = []
            self._replace_pictures(conn, int(item_id), pictures)

            conn.commit()
        finally:
            conn.close()

    def admin_delete_item(self, item_id: int) -> None:
        conn = get_connection()
        try:
            # Try to delete dependent records first to avoid FK issues.
            if self._table_exists(conn, "Picture"):
                conn.execute('DELETE FROM "Picture" WHERE ItemID = ?', (int(item_id),))
            if self._table_exists(conn, "Item_Category"):
                conn.execute('DELETE FROM "Item_Category" WHERE ItemID = ?', (int(item_id),))
            if self._table_exists(conn, "Item_Cart"):
                conn.execute('DELETE FROM "Item_Cart" WHERE ItemID = ?', (int(item_id),))
            if self._table_exists(conn, "Favorites"):
                conn.execute('DELETE FROM "Favorites" WHERE ItemID = ?', (int(item_id),))
            if self._table_exists(conn, "History"):
                conn.execute('DELETE FROM "History" WHERE ItemID = ?', (int(item_id),))

            cur = conn.execute('DELETE FROM "Item" WHERE ID = ?', (int(item_id),))
            conn.commit()
            if cur.rowcount == 0:
                raise AppError("Item not found")
        finally:
            conn.close()

    # ---------- UI-safe wrappers ----------

    def run(self, fn, *args, **kwargs) -> AppResult:
        try:
            return AppResult.success(fn(*args, **kwargs))
        except Exception as e:
            code, msg = map_exception(e)
            return AppResult.fail(code, msg)

    def ui_login(self, email: str, password: str) -> AppResult:
        return self.run(self.login, email, password)

    def ui_register_customer(self, username: str, email: str, name: str, password: str, currency: str = "EUR") -> AppResult:
        return self.run(self.register_customer, username, email, name, password, currency)

    # ---- Currency (UI-safe) ----

    def ui_list_supported_currencies(self) -> AppResult:
        return self.run(self.list_supported_currencies)

    def ui_get_customer_currency(self, user_id: int) -> AppResult:
        return self.run(self.get_customer_currency, user_id)

    def ui_set_customer_currency(self, user_id: int, currency: str) -> AppResult:
        return self.run(self.set_customer_currency, user_id, currency)

    # ---- Catalog (UI-safe) ----

    def ui_list_items(self, display_currency: Optional[str] = None) -> AppResult:
        return self.run(lambda: item_list_dto(self.list_items(display_currency=display_currency)))

    def ui_item_details(self, item_id: int) -> AppResult:
        return self.run(lambda: item_details_dto(self.get_item_details(item_id)))

    # ---- Cart / Orders (UI-safe) ----

    def ui_get_cart(self, customer_user_id: int, display_currency=None) -> AppResult:
        return self.run(lambda: cart_dto(self.get_cart(customer_user_id, display_currency)))

    def ui_add_to_cart(self, customer_user_id: int, item_id: int, quantity: int = 1) -> AppResult:
        return self.run(self.add_to_cart, customer_user_id, item_id, quantity)

    def ui_remove_from_cart(self, customer_user_id: int, item_id: int) -> AppResult:
        return self.run(self.remove_from_cart, customer_user_id, item_id)

    def ui_checkout(self, customer_user_id: int) -> AppResult:
        return self.run(self.proceed_to_checkout, customer_user_id)

    def ui_list_orders(self, customer_user_id: int, limit: int = 50) -> AppResult:
        return self.run(lambda: order_list_dto(self.list_orders(customer_user_id, limit)))

    def ui_order_details(self, customer_user_id: int, order_id: int) -> AppResult:
        return self.run(lambda: order_details_dto(self.get_order_details(customer_user_id, order_id)))

    def ui_remove_from_cart(self, customer_user_id: int, item_id: int) -> AppResult:
        return self.run(self.remove_from_cart, customer_user_id, item_id)

    # ---- ADMIN (UI-safe) ----

    def ui_admin_list_items(self) -> AppResult:
        return self.run(self.admin_list_items)

    def ui_admin_get_item(self, item_id: int) -> AppResult:
        return self.run(self.admin_get_item, item_id)

    def ui_admin_create_item(
        self,
        *,
        name: str,
        description: str,
        price: float,
        weight: float,
        length: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        pictures: Optional[List[str]] = None,
    ) -> AppResult:
        return self.run(
            self.admin_create_item,
            name=name,
            description=description,
            price=price,
            weight=weight,
            length=length,
            width=width,
            height=height,
            pictures=pictures,
        )

    def ui_admin_update_item(
        self,
        *,
        item_id: int,
        name: str,
        description: str,
        price: float,
        weight: float,
        length: float = 0.0,
        width: float = 0.0,
        height: float = 0.0,
        pictures: Optional[List[str]] = None,
    ) -> AppResult:
        return self.run(
            self.admin_update_item,
            item_id=item_id,
            name=name,
            description=description,
            price=price,
            weight=weight,
            length=length,
            width=width,
            height=height,
            pictures=pictures,
        )

    def ui_admin_delete_item(self, item_id: int) -> AppResult:
        return self.run(self.admin_delete_item, item_id)

    # ---------------- Favorites (UI-safe via direct SQL) ----------------

    def _ensure_customer(self, customer_user_id: int) -> None:
        conn = get_connection()
        try:
            row = conn.execute('SELECT UserID FROM "Customer" WHERE UserID = ?', (customer_user_id,)).fetchone()
            if not row:
                raise AppError("Customer not found")
        finally:
            conn.close()

    def ui_add_favorite(self, customer_user_id: int, item_id: int) -> AppResult:
        def op():
            self._ensure_customer(customer_user_id)
            conn = get_connection()
            try:
                it = conn.execute('SELECT ID FROM "Item" WHERE ID = ?', (int(item_id),)).fetchone()
                if not it:
                    raise AppError("Item not found")

                conn.execute(
                    'INSERT OR IGNORE INTO "Favorites"(CustomerUserID, ItemID) VALUES (?, ?)',
                    (int(customer_user_id), int(item_id)),
                )
                conn.commit()
                return True
            finally:
                conn.close()

        return self.run(op)

    def ui_remove_favorite(self, customer_user_id: int, item_id: int) -> AppResult:
        def op():
            self._ensure_customer(customer_user_id)
            conn = get_connection()
            try:
                conn.execute(
                    'DELETE FROM "Favorites" WHERE CustomerUserID = ? AND ItemID = ?',
                    (int(customer_user_id), int(item_id)),
                )
                conn.commit()
                return True
            finally:
                conn.close()

        return self.run(op)

    def ui_list_favorites(self, customer_user_id: int) -> AppResult:
        def op():
            self._ensure_customer(customer_user_id)
            conn = get_connection()
            try:
                cur = conn.execute(
                    """
                    SELECT i.ID as ItemID, i.Name as Name, i.Price as Price
                    FROM "Favorites" f
                    JOIN "Item" i ON i.ID = f.ItemID
                    WHERE f.CustomerUserID = ?
                    ORDER BY i.ID ASC
                    """,
                    (int(customer_user_id),),
                )
                return [
                    {"id": int(r["ItemID"]), "name": r["Name"], "price": float(r["Price"]), "currency": "EUR"}
                    for r in cur.fetchall()
                ]
            finally:
                conn.close()

        return self.run(op)

    # ---------------- History (UI-safe via direct SQL) ----------------

    def ui_record_view(self, customer_user_id: int, item_id: int) -> AppResult:
        def op():
            self._ensure_customer(customer_user_id)
            conn = get_connection()
            try:
                it = conn.execute('SELECT ID FROM "Item" WHERE ID = ?', (int(item_id),)).fetchone()
                if not it:
                    return True

                ts = datetime.now(timezone.utc).isoformat()
                conn.execute(
                    'INSERT INTO "History"(CustomerUserID, ItemID, ViewedAt) VALUES (?, ?, ?)',
                    (int(customer_user_id), int(item_id), ts),
                )
                conn.commit()
                return True
            finally:
                conn.close()

        return self.run(op)

    def ui_list_history(self, customer_user_id: int, limit: int = 50) -> AppResult:
        def op():
            self._ensure_customer(customer_user_id)
            conn = get_connection()
            try:
                cur = conn.execute(
                    """
                    SELECT h.ViewedAt as ViewedAt, i.ID as ItemID, i.Name as Name, i.Price as Price
                    FROM "History" h
                    JOIN "Item" i ON i.ID = h.ItemID
                    WHERE h.CustomerUserID = ?
                    ORDER BY h.ViewedAt DESC
                    LIMIT ?
                    """,
                    (int(customer_user_id), int(limit)),
                )
                return [
                    {
                        "viewed_at": r["ViewedAt"],
                        "item_id": int(r["ItemID"]),
                        "name": r["Name"],
                        "price": float(r["Price"]),
                        "currency": "EUR",
                    }
                    for r in cur.fetchall()
                ]
            finally:
                conn.close()

        return self.run(op)
