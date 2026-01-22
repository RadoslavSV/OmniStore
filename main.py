import time

from app.db.schema import init_db

from app.models.product import Dimensions
from app.models.item import Item

from app.repositories.user_repository import UserRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.history_repository import HistoryRepository

from app.services.auth_service import (
    AuthService,
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    InvalidCredentialsError,
)
from app.services.role_service import RoleService
from app.services.history_service import HistoryService


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

    # ---------- HISTORY ----------
    history_service = HistoryService(HistoryRepository(), item_repo)

    history_service.record_view(logged.id, item1_id)
    time.sleep(0.2)
    history_service.record_view(logged.id, item2_id)
    time.sleep(0.2)
    history_service.record_view(logged.id, item2_id)

    print("\nHistory list (newest first):")
    for row in history_service.list_history(logged.id):
        print(" -", row)

    # Uncomment to test clearing:
    # history_service.clear_history(logged.id)
    # print("\nHistory after clear:", history_service.list_history(logged.id))


if __name__ == "__main__":
    main()
