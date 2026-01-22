from app.db.schema import init_db

from app.models.product import Dimensions
from app.models.item import Item

from app.repositories.user_repository import UserRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.favorites_repository import FavoritesRepository

from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    InvalidCredentialsError,
)
from app.services.role_service import RoleService
from app.services.favorites_service import FavoritesService


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

    role_service = RoleService(AdminRepository(), CustomerRepository())
    role_service.make_customer(logged.id, currency="BGN")
    role_service.make_admin(logged.id)  # for item creation in this test

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

    # ---------- FAVORITES ----------
    fav_service = FavoritesService(FavoritesRepository(), item_repo)

    fav_service.add_favorite(logged.id, item1_id)
    fav_service.add_favorite(logged.id, item2_id)
    fav_service.add_favorite(logged.id, item2_id)  # duplicate is ignored by DB

    print("\nFavorites list:")
    for row in fav_service.list_favorites(logged.id):
        print(" -", row)

    print("\nIs lamp favorite?", fav_service.is_favorite(logged.id, item2_id))

    fav_service.remove_favorite(logged.id, item2_id)
    print("\nAfter removing lamp:")
    for row in fav_service.list_favorites(logged.id):
        print(" -", row)


if __name__ == "__main__":
    main()
