from app.db.schema import init_db

from app.models.product import Dimensions
from app.models.item import Item

from app.repositories.user_repository import UserRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.item_cart_repository import ItemCartRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.order_item_repository import OrderItemRepository

from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    InvalidCredentialsError,
)
from app.services.role_service import RoleService
from app.services.cart_service import CartService
from app.services.checkout_service import CheckoutService, EmptyCartError
from app.services.order_history_service import OrderHistoryService, OrderNotFoundError


def main():
    init_db()

    # ---------- AUTH ----------
    auth = AuthService(UserRepository())

    try:
        user = auth.register(
            username="radoslav",
            email="radoslav@example.com",
            name="Radoslav Velkov",
            password="secret123",
        )
        print("Registered:", user)
    except (EmailAlreadyExistsError, UsernameAlreadyExistsError) as e:
        print("Register skipped:", e)

    try:
        logged = auth.login(email="radoslav@example.com", password="secret123")
        print("Logged in:", logged)
    except InvalidCredentialsError as e:
        print("Login failed:", e)
        return

    # ---------- ROLES ----------
    role_service = RoleService(AdminRepository(), CustomerRepository())
    role_service.make_customer(logged.id, currency="EUR")
    role_service.make_admin(logged.id)

    # ---------- CREATE ITEMS ----------
    item_repo = ItemRepository()

    item1_id = item_repo.create(
        Item(
            id=None,
            admin_user_id=logged.id,
            name="Office Desk",
            description="Wooden office desk",
            dimensions=Dimensions(length=120, width=60, height=75),
            weight=25.5,
            price=300.00,
        )
    )
    item2_id = item_repo.create(
        Item(
            id=None,
            admin_user_id=logged.id,
            name="Desk Lamp",
            description="LED desk lamp",
            dimensions=Dimensions(length=20, width=12, height=35),
            weight=1.2,
            price=40.00,
        )
    )
    print("Created items:", item1_id, item2_id)

    # ---------- CART ----------
    cart_service = CartService(
        CartRepository(),
        ItemCartRepository(),
        item_repo,
        CustomerRepository(),
        base_currency="EUR",
    )

    cart_service.add_item(logged.id, item1_id, quantity=1)
    cart_service.add_item(logged.id, item2_id, quantity=2)
    print("\nCart total (EUR base):", cart_service.get_total(logged.id))

    # ---------- CHECKOUT (creates order + clears cart) ----------
    checkout = CheckoutService(
        CartRepository(),
        ItemCartRepository(),
        item_repo,
        OrderRepository(),
        OrderItemRepository(),
        base_currency="EUR",
    )

    try:
        order_id = checkout.checkout(logged.id)
        print("\nCheckout success. Created order id:", order_id)
    except EmptyCartError as e:
        print("Checkout failed:", e)

    print("Cart after checkout:", cart_service.get_items(logged.id))

    # ---------- ORDER HISTORY ----------
    history = OrderHistoryService(OrderRepository(), OrderItemRepository())

    print("\nOrder history:")
    orders = history.list_orders(logged.id)
    for o in orders:
        print(" -", o)

    if orders:
        first_order_id = orders[0]["order_id"]
        try:
            details = history.get_order_details(logged.id, first_order_id)
            print(f"\nOrder details for order {first_order_id}:")
            print("Order:", details["order"])
            print("Items:")
            for it in details["items"]:
                print(" -", it)
        except OrderNotFoundError as e:
            print("Details error:", e)


if __name__ == "__main__":
    main()
