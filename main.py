from app.db.schema import init_db

from app.models.product import Dimensions
from app.models.item import Item

from app.repositories.user_repository import UserRepository
from app.repositories.admin_repository import AdminRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.item_category_repository import ItemCategoryRepository

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

    # --------- ROLES: make ADMIN (required for Item FK) ---------
    role_service = RoleService(AdminRepository(), CustomerRepository())
    role_service.make_admin(logged.id)
    logged = role_service.enrich_user_role(logged)
    print("User role:", logged.role)

    # --------- CREATE CATEGORIES ---------
    cat_repo = CategoryRepository()

    def ensure_category(name: str) -> int:
        existing = cat_repo.get_by_name(name)
        if existing:
            return existing.id
        return cat_repo.create(name)

    furniture_id = ensure_category("Furniture")
    office_id = ensure_category("Office")

    print("Category ids:", {"Furniture": furniture_id, "Office": office_id})

    # --------- CREATE ITEM ---------
    item_repo = ItemRepository()

    dims = Dimensions(length=120.0, width=60.0, height=75.0)
    item = Item(
        id=None,
        admin_user_id=logged.id,
        name="Office Desk",
        description="Wooden office desk with drawers",
        dimensions=dims,
        weight=25.5,
        price=299.99,
    )

    item_id = item_repo.create(item)
    print("Created item id:", item_id)

    # --------- LINK ITEM <-> CATEGORY ---------
    ic_repo = ItemCategoryRepository()
    ic_repo.add(item_id, furniture_id)
    ic_repo.add(item_id, office_id)

    cats_for_item = ic_repo.list_categories_for_item(item_id)
    print(f"Categories for item {item_id}:")
    for c in cats_for_item:
        print(" -", c)

    items_for_furniture = ic_repo.list_items_for_category(furniture_id)
    print(f"Items in category 'Furniture' (id={furniture_id}):")
    for it in items_for_furniture:
        print(" -", it)


if __name__ == "__main__":
    main()
