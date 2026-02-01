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
    # ADMIN: Manage Items (CRUD via direct SQL) - MATCHES YOUR SCHEMA
    # Item(AdminUserID, Name, Description, Height, Width, Depth, Weight, Price)
    # Picture(ItemID, FilePath, IsMain)
    # ============================================================

    def admin_list_items(self) -> List[Dict]:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                SELECT ID, Name, Price, Weight
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
            r = conn.execute(
                """
                SELECT ID, AdminUserID, Name, Description, Height, Width, Depth, Weight, Price
                FROM "Item"
                WHERE ID = ?
                """,
                (int(item_id),),
            ).fetchone()
            if not r:
                raise AppError("Item not found")

            pics = conn.execute(
                """
                SELECT FilePath
                FROM "Picture"
                WHERE ItemID = ?
                ORDER BY IsMain DESC, ID ASC
                """,
                (int(item_id),),
            ).fetchall()
            pictures = [p["FilePath"] for p in pics] if pics else []

            # Map schema -> UI keys:
            # length -> Depth, width -> Width, height -> Height
            return {
                "id": int(r["ID"]),
                "admin_user_id": int(r["AdminUserID"]),
                "name": r["Name"],
                "description": r["Description"],
                "price": float(r["Price"]),
                "weight": float(r["Weight"]),
                "length": float(r["Depth"]),
                "width": float(r["Width"]),
                "height": float(r["Height"]),
                "pictures": pictures,
                "currency": "EUR",
            }
        finally:
            conn.close()

    def _replace_pictures(self, conn, item_id: int, pictures: Optional[List[str]]) -> None:
        pictures = pictures or []

        # normalize -> store as images/<filename>
        norm: List[str] = []
        for p in pictures:
            p = str(p or "").strip()
            if not p:
                continue
            p = p.replace("\\", "/")
            if p.lower().startswith("images/"):
                p = p.split("/", 1)[1]
            norm.append(f"images/{p}")

        # delete existing
        conn.execute('DELETE FROM "Picture" WHERE ItemID = ?', (int(item_id),))

        # insert new (first = main)
        for idx, fp in enumerate(norm):
            is_main = 1 if idx == 0 else 0
            conn.execute(
                'INSERT INTO "Picture"(ItemID, FilePath, IsMain) VALUES (?, ?, ?)',
                (int(item_id), fp, int(is_main)),
            )

    def admin_create_item(
        self,
        *,
        admin_user_id: int,
        name: str,
        description: str,
        price: float,
        weight: float,
        length: float,
        width: float,
        height: float,
        pictures: Optional[List[str]] = None,
    ) -> int:
        """
        length -> Depth
        width  -> Width
        height -> Height
        """
        if not admin_user_id:
            raise AppError("Admin user is required")

        conn = get_connection()
        try:
            # Ensure admin exists (FK would fail anyway, but this gives nicer message)
            row = conn.execute('SELECT UserID FROM "Admin" WHERE UserID = ?', (int(admin_user_id),)).fetchone()
            if not row:
                raise AppError("Admin not found in DB (ensure_admin missing?)")

            cur = conn.execute(
                """
                INSERT INTO "Item"(AdminUserID, Name, Description, Height, Width, Depth, Weight, Price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(admin_user_id),
                    str(name),
                    str(description),
                    float(height),
                    float(width),
                    float(length),
                    float(weight),
                    float(price),
                ),
            )
            item_id = int(cur.lastrowid)

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
        length: float,
        width: float,
        height: float,
        pictures: Optional[List[str]] = None,
    ) -> None:
        conn = get_connection()
        try:
            cur = conn.execute(
                """
                UPDATE "Item"
                SET Name = ?, Description = ?, Height = ?, Width = ?, Depth = ?, Weight = ?, Price = ?
                WHERE ID = ?
                """,
                (
                    str(name),
                    str(description),
                    float(height),
                    float(width),
                    float(length),
                    float(weight),
                    float(price),
                    int(item_id),
                ),
            )
            if cur.rowcount == 0:
                raise AppError("Item not found")

            self._replace_pictures(conn, int(item_id), pictures)

            conn.commit()
        finally:
            conn.close()

    def admin_delete_item(self, item_id: int) -> None:
        conn = get_connection()
        try:
            # delete dependent first (safe; FK would also cascade on Picture/Item_Category, but keep explicit)
            conn.execute('DELETE FROM "Picture" WHERE ItemID = ?', (int(item_id),))
            conn.execute('DELETE FROM "Item_Category" WHERE ItemID = ?', (int(item_id),))
            conn.execute('DELETE FROM "Item_Cart" WHERE ItemID = ?', (int(item_id),))
            conn.execute('DELETE FROM "Favorites" WHERE ItemID = ?', (int(item_id),))
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

    # ---- ADMIN (UI-safe) ----

    def ui_admin_list_items(self) -> AppResult:
        return self.run(self.admin_list_items)

    def ui_admin_get_item(self, item_id: int) -> AppResult:
        return self.run(self.admin_get_item, item_id)

    def ui_admin_create_item(
        self,
        *,
        admin_user_id: int,
        name: str,
        description: str,
        price: float,
        weight: float,
        length: float,
        width: float,
        height: float,
        pictures: Optional[List[str]] = None,
    ) -> AppResult:
        return self.run(
            self.admin_create_item,
            admin_user_id=admin_user_id,
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
        length: float,
        width: float,
        height: float,
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
