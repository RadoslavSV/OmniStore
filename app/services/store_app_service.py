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
    - Currency API calls are controlled internally by CartService/CurrencyService flags.
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
            base_currency="EUR",
        )

    # ---------- Auth / Roles ----------

    def register_customer(self, username: str, email: str, name: str, password: str, currency: str = "EUR") -> User:
        user = self.auth.register(username=username, email=email, name=name, password=password)
        self.roles.make_customer(user.id, currency=currency)
        return self.roles.enrich_user_role(user)

    def login(self, email: str, password: str) -> User:
        user = self.auth.login(email=email, password=password)
        return self.roles.enrich_user_role(user)

    def ensure_admin(self, user_id: int) -> None:
        self.roles.make_admin(user_id)

    def set_customer_currency(self, user_id: int, currency: str) -> None:
        self.customer_repo.set_currency(user_id, currency)

    def get_customer_currency(self, user_id: int) -> str:
        return (self.customer_repo.get_currency(user_id) or self.base_currency).upper()

    # ---------- Catalog ----------

    def list_items(self) -> List[Dict]:
        items = self.item_repo.list_all() or []
        return [
            {"item_id": it.id, "name": it.name, "price_base": float(it.price), "currency": self.base_currency}
            for it in items
        ]

    def get_item_details(self, item_id: int) -> dict:
        """
        Returns a structure that item_details_dto expects:
        {
          "item": <Item model>,
          "categories": [str, ...],
          "pictures": [str, ...],          # file paths
          "main_picture": str | None       # file path
        }
        """
        item = self.item_repo.get_by_id(item_id)
        if not item:
            raise AppError("Item not found")

        # Use direct SQL to avoid repo-method-name mismatches
        conn = get_connection()
        try:
            # Categories (names)
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

            # Pictures (paths)
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
        """
        Proceed to checkout = successful purchase (no payment simulation).
        Creates order snapshot and empties cart.
        """
        return self.checkout.checkout(customer_user_id)

    def list_orders(self, customer_user_id: int, limit: int = 50) -> List[Dict]:
        return self.order_history.list_orders(customer_user_id, limit=limit)

    def get_order_details(self, customer_user_id: int, order_id: int) -> Dict:
        return self.order_history.get_order_details(customer_user_id, order_id)

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

    def ui_list_items(self) -> AppResult:
        return self.run(lambda: item_list_dto(self.list_items()))

    def ui_item_details(self, item_id: int) -> AppResult:
        return self.run(lambda: item_details_dto(self.get_item_details(item_id)))

    def ui_get_cart(self, customer_user_id: int, display_currency=None) -> AppResult:
        return self.run(lambda: cart_dto(self.get_cart(customer_user_id, display_currency)))

    def ui_add_to_cart(self, customer_user_id: int, item_id: int, quantity: int = 1) -> AppResult:
        return self.run(self.add_to_cart, customer_user_id, item_id, quantity)

    def ui_checkout(self, customer_user_id: int) -> AppResult:
        return self.run(self.proceed_to_checkout, customer_user_id)

    def ui_list_orders(self, customer_user_id: int, limit: int = 50) -> AppResult:
        return self.run(lambda: order_list_dto(self.list_orders(customer_user_id, limit)))

    def ui_order_details(self, customer_user_id: int, order_id: int) -> AppResult:
        return self.run(lambda: order_details_dto(self.get_order_details(customer_user_id, order_id)))

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
