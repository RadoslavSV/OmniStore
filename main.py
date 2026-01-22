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


def main():
    init_db()

    # --------- AUTH ---------
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

    # --------- ROLES ---------
    role_service = RoleService(AdminRepository(), CustomerRepository())

    # We need CUSTOMER for Cart FK
    role_service.make_customer(logged.id, currency="BGN")
    logged = role_service.enrich_user_role(logged)
    print("User role:", logged.role)

    # --------- CREATE CART (for customer) ---------
    cart_repo = CartRepository()
    cart = cart_repo.get_or_create_for_customer(logged.id)
    print("Cart:", cart)

    # --------- CREATE ITEMS (needs ADMIN for Item FK) ---------
    # Make the same user admin just for testing item creation
    role_service.make_admin(logged.id)

    item_repo = ItemRepository()
    item1_id = item_repo.create(
        Item(
            id=None,
            admin_user_id=logged.id,
            name="Office Desk",
            description="Wooden office desk",
            dimensions=Dimensions(length=120, width=60, height=75),
            weight=25.5,
            price=299.99,
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
            price=39.90,
        )
    )
    print("Created items:", item1_id, item2_id)

    # --------- ADD ITEMS TO CART ---------
    ic_repo = ItemCartRepository()

    ic_repo.upsert_quantity(cart.id, item1_id, 2)
    ic_repo.upsert_quantity(cart.id, item2_id, 1)

    # increment lamp by +2 (=> 3)
    ic_repo.increment(cart.id, item2_id, delta=2)

    # decrement desk by 1 (=> 1)
    ic_repo.decrement(cart.id, item1_id, delta=1)

    print("Cart items:")
    for ci in ic_repo.list_items(cart.id):
        print(" -", ci)


if __name__ == "__main__":
    main()
