from app.db.schema import init_db

from app.models.product import Dimensions
from app.models.item import Item

from app.repositories.user_repository import UserRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.cart_repository import CartRepository
from app.repositories.item_cart_repository import ItemCartRepository

from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    InvalidCredentialsError,
)
from app.services.role_service import RoleService
from app.services.cart_service import CartService


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
    role_service.make_customer(logged.id, currency="USD")  # customer prefers USD display
    role_service.make_admin(logged.id)  # to create items in this test

    # ---------- CREATE ITEMS (prices in EUR) ----------
    item_repo = ItemRepository()

    item1_id = item_repo.create(
        Item(
            id=None,
            admin_user_id=logged.id,
            name="Office Desk",
            description="Wooden office desk",
            dimensions=Dimensions(length=120, width=60, height=75),
            weight=25.5,
            price=300.00,  # EUR
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
            price=40.00,  # EUR
        )
    )
    print("Created items:", item1_id, item2_id)

    # ---------- CART SERVICE ----------
    cart_service = CartService(
        CartRepository(),
        ItemCartRepository(),
        item_repo,
        CustomerRepository(),
        base_currency="EUR",
    )

    cart_service.add_item(logged.id, item1_id, quantity=1)
    cart_service.add_item(logged.id, item2_id, quantity=3)

    print("\nCart items (customer currency = USD):")
    for row in cart_service.get_detailed_items(logged.id):
        print(" -", row)

    print("Cart total (USD):", cart_service.get_total(logged.id))

    print("\nCart items (forced GBP):")
    for row in cart_service.get_detailed_items(logged.id, display_currency="GBP"):
        print(" -", row)

    print("Cart total (GBP):", cart_service.get_total(logged.id, display_currency="GBP"))


if __name__ == "__main__":
    main()
