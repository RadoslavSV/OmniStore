from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict

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


@dataclass
class StoreAppService:
    """
    Facade used by UI layer.
    UI should talk ONLY to this service (no direct repository access).

    Notes:
    - Currency API calls are controlled internally by CartService/CurrencyService flags.
    - Prices in DB are base currency EUR (snapshot in orders).
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
        """
        Create a fully wired instance with default repositories/services.
        UI can call StoreAppService.create_default() once and reuse it.
        """
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
        items = self.item_repo.get_all()
        return [
            {
                "item_id": it.id,
                "name": it.name,
                "price_base": float(it.price),
                "currency": self.base_currency,
            }
            for it in items
        ]

    def get_item_details(self, item_id: int) -> Dict:
        it = self.item_repo.get_by_id(item_id)
        if it is None:
            raise AppError("Item not found")

        cats = self.item_category_repo.get_categories_for_item(item_id)
        pics = self.picture_repo.get_pictures_for_item(item_id)
        main_pic = self.picture_repo.get_main_picture(item_id)

        return {
            "item": {
                "item_id": it.id,
                "name": it.name,
                "description": it.description,
                "price_base": float(it.price),
                "currency": self.base_currency,
                "dimensions": {
                    "length": it.dimensions.length,
                    "width": it.dimensions.width,
                    "height": it.dimensions.height,
                },
                "weight": it.weight,
            },
            "categories": [{"id": c.id, "name": c.name} for c in cats],
            "pictures": [{"id": p.id, "file_path": p.file_path, "is_main": p.is_main} for p in pics],
            "main_picture": {"id": main_pic.id, "file_path": main_pic.file_path} if main_pic else None,
        }

    # ---------- Favorites ----------

    def add_favorite(self, customer_user_id: int, item_id: int) -> None:
        self.favorites.add_favorite(customer_user_id, item_id)

    def remove_favorite(self, customer_user_id: int, item_id: int) -> None:
        self.favorites.remove_favorite(customer_user_id, item_id)

    def list_favorites(self, customer_user_id: int) -> List[Dict]:
        return self.favorites.list_favorites(customer_user_id)

    def is_favorite(self, customer_user_id: int, item_id: int) -> bool:
        return self.favorites.is_favorite(customer_user_id, item_id)

    # ---------- History ----------

    def record_view(self, customer_user_id: int, item_id: int) -> None:
        self.history.record_view(customer_user_id, item_id)

    def list_history(self, customer_user_id: int, limit: int = 50) -> List[Dict]:
        return self.history.list_history(customer_user_id, limit=limit)

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
        Your chosen behavior:
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
        """
        Execute an operation and return AppResult (no exceptions bubble to UI).
        """
        try:
            return AppResult.success(fn(*args, **kwargs))
        except Exception as e:
            code, msg = map_exception(e)
            return AppResult.fail(code, msg)

    # Examples UI can call:
    def ui_login(self, email: str, password: str) -> AppResult:
        return self.run(self.login, email, password)

    def ui_register_customer(self, username: str, email: str, name: str, password: str, currency: str = "EUR") -> AppResult:
        return self.run(self.register_customer, username, email, name, password, currency)

    def ui_list_items(self) -> AppResult:
        return self.run(self.list_items)

    def ui_get_cart(self, customer_user_id: int, display_currency: Optional[str] = None) -> AppResult:
        return self.run(self.get_cart, customer_user_id, display_currency)

    def ui_add_to_cart(self, customer_user_id: int, item_id: int, quantity: int = 1) -> AppResult:
        return self.run(self.add_to_cart, customer_user_id, item_id, quantity)

    def ui_checkout(self, customer_user_id: int) -> AppResult:
        return self.run(self.proceed_to_checkout, customer_user_id)

    def ui_list_orders(self, customer_user_id: int, limit: int = 50) -> AppResult:
        return self.run(self.list_orders, customer_user_id, limit)

    def ui_order_details(self, customer_user_id: int, order_id: int) -> AppResult:
        return self.run(self.get_order_details, customer_user_id, order_id)
