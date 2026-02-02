import pytest

from app.services.checkout_service import CheckoutService, EmptyCartError
from app.models.order_item import OrderItem

class CartItemLike:
    def __init__(self, item_id: int, quantity: int):
        self.item_id = item_id
        self.quantity = quantity

class FakeOrderRepo:
    def __init__(self):
        self.created = []
        self.updated_totals = []

    def create(self, customer_user_id: int, created_at: str, status: str, total_base: float):
        # return deterministic order_id
        order_id = 123
        self.created.append((customer_user_id, created_at, status, total_base))
        return order_id

    def update_total_base(self, order_id: int, total_base: float):
        self.updated_totals.append((order_id, total_base))


class FakeOrderItemRepo:
    def __init__(self):
        self.added = []

    def add(self, order_item):
        self.added.append(order_item)


def make_service(cart_items, items):
    svc = CheckoutService(
        cart_repo=FakeCartRepo(cart_id=10),
        item_cart_repo=FakeItemCartRepo(cart_items),
        item_repo=FakeItemRepo(items),
        order_repo=FakeOrderRepo(),
        order_item_repo=FakeOrderItemRepo(),
        base_currency="EUR",
    )
    return svc


def test_checkout_raises_when_cart_empty():
    svc = make_service(cart_items=[], items={})

    with pytest.raises(EmptyCartError):
        svc.checkout(customer_user_id=1)


def test_checkout_creates_order_and_order_items_and_updates_total(monkeypatch):
    cart_items = [CartItemLike(1, 2), CartItemLike(2, 1)]
    items = {
        1: FakeItem(1, "Desk", 100.0),
        2: FakeItem(2, "Lamp", 50.0),
    }

    svc = make_service(cart_items=cart_items, items=items)

    # Avoid real DB in _clear_cart:
    called = {"cart_id": None}

    def fake_clear(cart_id: int):
        called["cart_id"] = cart_id

    svc._clear_cart = fake_clear

    order_id = svc.checkout(customer_user_id=99)

    assert order_id == 123

    # Validate order repo usage
    assert len(svc.order_repo.created) == 1
    assert svc.order_repo.created[0][0] == 99  # customer_user_id
    assert svc.order_repo.created[0][2] == "CREATED"  # status

    # Validate order item snapshots
    assert len(svc.order_item_repo.added) == 2
    names = sorted([oi.item_name for oi in svc.order_item_repo.added])
    assert names == ["Desk", "Lamp"]

    # Total: 2*100 + 1*50 = 250
    assert svc.order_repo.updated_totals == [(123, 250.0)]

    # Cart cleared for correct cart id
    assert called["cart_id"] == 10


class FakeCart:
    def __init__(self, cart_id):
        self.id = cart_id


class FakeCartRepo:
    def __init__(self, cart_id=1):
        self.cart = FakeCart(cart_id)

    def get_or_create_for_customer(self, customer_user_id: int):
        return self.cart


class FakeItemCartRepo:
    def __init__(self, items):
        self._items = items

    def list_items(self, cart_id: int):
        return self._items


class FakeCartItem:
    def __init__(self, item_id, quantity):
        self.item_id = item_id
        self.quantity = quantity


class FakeItem:
    def __init__(self, item_id, name, price):
        self.id = item_id
        self.name = name
        self.price = price


class FakeItemRepo:
    def __init__(self, items_by_id):
        self.items_by_id = items_by_id

    def get_by_id(self, item_id: int):
        return self.items_by_id.get(item_id)


class FakeOrderRepo:
    def __init__(self):
        self.created = []
        self.updated = []

    def create(self, customer_user_id, created_at, status="CREATED", total_base=0.0):
        self.created.append(
            {"customer_user_id": customer_user_id, "created_at": created_at, "status": status, "total_base": total_base}
        )
        return 123  # order_id

    def update_total_base(self, order_id: int, total_base: float):
        self.updated.append({"order_id": order_id, "total_base": total_base})


class FakeOrderItemRepo:
    def __init__(self):
        self.added = []

    def add(self, order_item: OrderItem):
        self.added.append(order_item)


def test_checkout_raises_when_cart_empty(monkeypatch):
    svc = CheckoutService(
        cart_repo=FakeCartRepo(),
        item_cart_repo=FakeItemCartRepo(items=[]),
        item_repo=FakeItemRepo(items_by_id={}),
        order_repo=FakeOrderRepo(),
        order_item_repo=FakeOrderItemRepo(),
        base_currency="EUR",
    )

    with pytest.raises(EmptyCartError):
        svc.checkout(customer_user_id=1)


def test_checkout_creates_order_and_items_and_updates_total(monkeypatch):
    cart_items = [
        FakeCartItem(item_id=1, quantity=2),
        FakeCartItem(item_id=2, quantity=1),
    ]

    item_repo = FakeItemRepo(
        {
            1: FakeItem(1, "Desk", 300.0),
            2: FakeItem(2, "Lamp", 40.0),
        }
    )

    order_repo = FakeOrderRepo()
    order_item_repo = FakeOrderItemRepo()

    svc = CheckoutService(
        cart_repo=FakeCartRepo(cart_id=10),
        item_cart_repo=FakeItemCartRepo(items=cart_items),
        item_repo=item_repo,
        order_repo=order_repo,
        order_item_repo=order_item_repo,
        base_currency="EUR",
    )

    # avoid sqlite side-effect
    cleared = {"called": False, "cart_id": None}
    def fake_clear(cart_id: int):
        cleared["called"] = True
        cleared["cart_id"] = cart_id

    monkeypatch.setattr(svc, "_clear_cart", fake_clear)

    order_id = svc.checkout(customer_user_id=5)

    assert order_id == 123
    assert len(order_repo.created) == 1
    assert len(order_item_repo.added) == 2
    assert len(order_repo.updated) == 1

    # total_base: 2*300 + 1*40 = 640.0
    assert order_repo.updated[0]["order_id"] == 123
    assert order_repo.updated[0]["total_base"] == 640.0

    assert cleared["called"] is True
    assert cleared["cart_id"] == 10


def test_checkout_skips_missing_items(monkeypatch):
    cart_items = [
        FakeCartItem(item_id=1, quantity=2),
        FakeCartItem(item_id=999, quantity=1),  # missing
    ]

    item_repo = FakeItemRepo({1: FakeItem(1, "Desk", 300.0)})
    order_repo = FakeOrderRepo()
    order_item_repo = FakeOrderItemRepo()

    svc = CheckoutService(
        cart_repo=FakeCartRepo(cart_id=7),
        item_cart_repo=FakeItemCartRepo(items=cart_items),
        item_repo=item_repo,
        order_repo=order_repo,
        order_item_repo=order_item_repo,
        base_currency="EUR",
    )

    monkeypatch.setattr(svc, "_clear_cart", lambda _cid: None)

    order_id = svc.checkout(customer_user_id=1)

    assert order_id == 123
    assert len(order_item_repo.added) == 1  # only the existing item
    assert order_repo.updated[0]["total_base"] == 600.0  # 2*300
