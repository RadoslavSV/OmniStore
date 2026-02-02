import types
import pytest

import app.services.cart_service as cart_service_mod
from app.services.cart_service import CartService, InvalidQuantityError, ItemNotFoundError


# ---------------- Helpers (simple fakes) ----------------

class FakeCart:
    def __init__(self, cart_id: int):
        self.id = cart_id


class FakeItem:
    def __init__(self, item_id: int, name: str, price: float):
        self.id = item_id
        self.name = name
        self.price = price


class FakeCartRepo:
    def __init__(self, cart_id: int = 1):
        self.cart = FakeCart(cart_id)

    def get_or_create_for_customer(self, customer_user_id: int):
        return self.cart


class CartItemLike:
    def __init__(self, item_id: int, quantity: int):
        self.item_id = item_id
        self.quantity = quantity


class FakeItemCartRepo:
    def __init__(self):
        self.increment_calls = []
        self.upsert_calls = []
        self.remove_calls = []
        self.items_by_cart = {}  # cart_id -> list[CartItemLike]

    def increment(self, cart_id: int, item_id: int, delta: int):
        self.increment_calls.append((cart_id, item_id, delta))

    def upsert_quantity(self, cart_id: int, item_id: int, quantity: int):
        self.upsert_calls.append((cart_id, item_id, quantity))

    def remove_item(self, cart_id: int, item_id: int):
        self.remove_calls.append((cart_id, item_id))

    def list_items(self, cart_id: int):
        return list(self.items_by_cart.get(cart_id, []))


class FakeCustomerRepo:
    def __init__(self, currency="EUR"):
        self._currency = currency

    def get_currency(self, customer_user_id: int):
        return self._currency


class FakeItemRepo:
    def __init__(self, items: dict[int, FakeItem]):
        self.items = dict(items)

    def get_by_id(self, item_id: int):
        return self.items.get(item_id)


def make_service(*, items=None, customer_currency="EUR", cart_id=1):
    items = items or {}
    cart_repo = FakeCartRepo(cart_id=cart_id)
    item_cart_repo = FakeItemCartRepo()
    item_repo = FakeItemRepo(items)
    customer_repo = FakeCustomerRepo(currency=customer_currency)

    svc = CartService(
        cart_repo=cart_repo,
        item_cart_repo=item_cart_repo,
        item_repo=item_repo,
        customer_repo=customer_repo,
        base_currency="EUR",
    )
    return svc, cart_repo, item_cart_repo, item_repo, customer_repo


# ---------------- Tests ----------------

def test_add_item_rejects_non_positive_quantity():
    svc, *_ = make_service(items={1: FakeItem(1, "Desk", 300.0)})

    with pytest.raises(InvalidQuantityError):
        svc.add_item(customer_user_id=10, item_id=1, quantity=0)

    with pytest.raises(InvalidQuantityError):
        svc.add_item(customer_user_id=10, item_id=1, quantity=-5)


def test_add_item_raises_when_item_missing():
    svc, *_ = make_service(items={})

    with pytest.raises(ItemNotFoundError):
        svc.add_item(customer_user_id=10, item_id=999, quantity=1)


def test_add_item_calls_increment_on_item_cart_repo():
    svc, _, item_cart_repo, *_ = make_service(items={1: FakeItem(1, "Desk", 300.0)}, cart_id=7)

    svc.add_item(customer_user_id=10, item_id=1, quantity=3)

    assert item_cart_repo.increment_calls == [(7, 1, 3)]


def test_set_quantity_rejects_non_positive_quantity():
    svc, *_ = make_service(items={1: FakeItem(1, "Desk", 300.0)})

    with pytest.raises(InvalidQuantityError):
        svc.set_quantity(customer_user_id=10, item_id=1, quantity=0)


def test_set_quantity_calls_upsert_quantity():
    svc, _, item_cart_repo, *_ = make_service(items={1: FakeItem(1, "Desk", 300.0)}, cart_id=5)

    svc.set_quantity(customer_user_id=10, item_id=1, quantity=9)

    assert item_cart_repo.upsert_calls == [(5, 1, 9)]


def test_remove_item_calls_remove_item():
    svc, _, item_cart_repo, *_ = make_service(items={1: FakeItem(1, "Desk", 300.0)}, cart_id=2)

    svc.remove_item(customer_user_id=10, item_id=1)

    assert item_cart_repo.remove_calls == [(2, 1)]


def test_get_detailed_items_skips_deleted_items(monkeypatch):
    svc, _, item_cart_repo, *_ = make_service(items={1: FakeItem(1, "Desk", 300.0)}, cart_id=1)

    # cart has item 1 and item 999 (deleted)
    item_cart_repo.items_by_cart[1] = [CartItemLike(1, 2), CartItemLike(999, 3)]

    # Make currency API "disabled"
    monkeypatch.setattr(cart_service_mod, "currency_service", types.SimpleNamespace(access_key=None), raising=True)

    rows = svc.get_detailed_items(customer_user_id=10, display_currency="USD")

    assert len(rows) == 1
    assert rows[0]["item_id"] == 1
    assert rows[0]["quantity"] == 2


def test_get_detailed_items_when_api_disabled_forces_eur(monkeypatch):
    svc, _, item_cart_repo, *_ = make_service(
        items={1: FakeItem(1, "Desk", 300.0), 2: FakeItem(2, "Lamp", 40.0)},
        cart_id=1,
    )
    item_cart_repo.items_by_cart[1] = [CartItemLike(1, 1), CartItemLike(2, 2)]

    monkeypatch.setattr(cart_service_mod, "currency_service", types.SimpleNamespace(access_key=None), raising=True)

    rows = svc.get_detailed_items(customer_user_id=10, display_currency="USD")

    assert rows[0]["currency"] == "EUR"
    assert rows[0]["unit_price"] == 300.0
    assert rows[0]["subtotal"] == 300.0

    assert rows[1]["currency"] == "EUR"
    assert rows[1]["unit_price"] == 40.0
    assert rows[1]["subtotal"] == 80.0


def test_get_detailed_items_when_api_enabled_converts_prices(monkeypatch):
    svc, _, item_cart_repo, *_ = make_service(items={1: FakeItem(1, "Desk", 300.0)}, cart_id=1)
    item_cart_repo.items_by_cart[1] = [CartItemLike(1, 2)]  # subtotal_base=600

    class FakeCurrencyService:
        access_key = "key"

        def convert(self, amount, to_currency, from_currency):
            return round(float(amount) * 2.0, 2)  # EUR->USD = x2 for test

    monkeypatch.setattr(cart_service_mod, "currency_service", FakeCurrencyService(), raising=True)

    rows = svc.get_detailed_items(customer_user_id=10, display_currency="USD")

    assert len(rows) == 1
    r = rows[0]
    assert r["currency"] == "USD"
    assert r["unit_price_base"] == 300.0
    assert r["subtotal_base"] == 600.0
    assert r["unit_price"] == 600.0
    assert r["subtotal"] == 1200.0


def test_get_total_sums_subtotals_base_and_converts_when_api_enabled(monkeypatch):
    svc, _, item_cart_repo, *_ = make_service(
        items={1: FakeItem(1, "Desk", 100.0), 2: FakeItem(2, "Lamp", 50.0)},
        cart_id=1,
    )
    item_cart_repo.items_by_cart[1] = [CartItemLike(1, 2), CartItemLike(2, 1)]  # base=250

    class FakeCurrencyService:
        access_key = "key"

        def convert(self, amount, to_currency, from_currency):
            return round(float(amount) * 1.5, 2)  # EUR->USD

    monkeypatch.setattr(cart_service_mod, "currency_service", FakeCurrencyService(), raising=True)

    total = svc.get_total(customer_user_id=10, display_currency="USD")

    assert total["total_base"] == 250.0
    assert total["currency"] == "USD"
    assert total["total"] == 375.0
