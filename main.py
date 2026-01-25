from app.db.schema import init_db
from app.services.store_app_service import StoreAppService


def main():
    init_db()

    app = StoreAppService.create_default()

    print("\n=== REGISTER ===")
    r = app.ui_register_customer(
        username="radoslav",
        email="radoslav@example.com",
        name="Radoslav Velkov",
        password="secret123",
        currency="EUR",
    )
    print(r)

    print("\n=== REGISTER (duplicate email, expect error) ===")
    r = app.ui_register_customer(
        username="radoslav2",
        email="radoslav@example.com",
        name="Test",
        password="123",
        currency="EUR",
    )
    print(r)

    print("\n=== LOGIN ===")
    r = app.ui_login("radoslav@example.com", "secret123")
    print(r)
    if not r.ok:
        return

    user = r.data
    user_id = user.id

    print("\n=== LIST ITEMS (empty catalog) ===")
    r = app.ui_list_items()
    print(r)

    print("\n=== ADD TO CART (invalid item, expect error) ===")
    r = app.ui_add_to_cart(user_id, item_id=999, quantity=1)
    print(r)

    print("\n=== GET CART ===")
    r = app.ui_get_cart(user_id)
    print(r)

    print("\n=== CHECKOUT (empty cart, expect error) ===")
    r = app.ui_checkout(user_id)
    print(r)

    print("\n=== LIST ORDERS (should be empty) ===")
    r = app.ui_list_orders(user_id)
    print(r)


if __name__ == "__main__":
    main()
