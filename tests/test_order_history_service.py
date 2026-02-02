import pytest

from app.services.order_history_service import OrderHistoryService, OrderNotFoundError


class OrderLike:
    def __init__(self, order_id, customer_user_id, created_at, status, total_base):
        self.id = order_id
        self.customer_user_id = customer_user_id
        self.created_at = created_at
        self.status = status
        self.total_base = total_base


class OrderItemLike:
    def __init__(self, item_id, item_name, unit_price_base, quantity):
        self.item_id = item_id
        self.item_name = item_name
        self.unit_price_base = unit_price_base
        self.quantity = quantity


class FakeOrderRepo:
    def __init__(self, orders_by_customer=None, by_id=None):
        self.orders_by_customer = orders_by_customer or {}
        self.by_id = by_id or {}

    def list_for_customer(self, customer_user_id: int, limit: int = 50):
        return list(self.orders_by_customer.get(customer_user_id, []))[:limit]

    def get_by_id(self, order_id: int):
        return self.by_id.get(order_id)


class FakeOrderItemRepo:
    def __init__(self, items_by_order=None):
        self.items_by_order = items_by_order or {}

    def list_for_order(self, order_id: int):
        return list(self.items_by_order.get(order_id, []))


def test_list_orders_maps_fields_correctly():
    o1 = OrderLike(1, 10, "2025-01-01T10:00:00Z", "CREATED", 250.0)
    o2 = OrderLike(2, 10, "2025-01-02T10:00:00Z", "PAID", 100.0)

    order_repo = FakeOrderRepo(orders_by_customer={10: [o1, o2]})
    item_repo = FakeOrderItemRepo()

    svc = OrderHistoryService(order_repo=order_repo, order_item_repo=item_repo)

    rows = svc.list_orders(10, limit=50)

    assert len(rows) == 2
    assert rows[0]["order_id"] == 1
    assert rows[0]["currency"] == "EUR"
    assert rows[1]["status"] == "PAID"
    assert rows[1]["total_base"] == 100.0


def test_get_order_details_raises_if_order_missing():
    svc = OrderHistoryService(order_repo=FakeOrderRepo(by_id={}), order_item_repo=FakeOrderItemRepo())

    with pytest.raises(OrderNotFoundError):
        svc.get_order_details(customer_user_id=10, order_id=999)


def test_get_order_details_raises_if_order_belongs_to_other_customer():
    order = OrderLike(1, 999, "2025-01-01", "CREATED", 10.0)  # customer_user_id != 10
    svc = OrderHistoryService(order_repo=FakeOrderRepo(by_id={1: order}), order_item_repo=FakeOrderItemRepo())

    with pytest.raises(OrderNotFoundError):
        svc.get_order_details(customer_user_id=10, order_id=1)


def test_get_order_details_returns_order_and_items_with_subtotals():
    order = OrderLike(1, 10, "2025-01-01", "CREATED", 250.0)
    items = [
        OrderItemLike(item_id=5, item_name="Desk", unit_price_base=100.0, quantity=2),
        OrderItemLike(item_id=6, item_name="Lamp", unit_price_base=50.0, quantity=1),
    ]

    svc = OrderHistoryService(
        order_repo=FakeOrderRepo(by_id={1: order}),
        order_item_repo=FakeOrderItemRepo(items_by_order={1: items}),
    )

    details = svc.get_order_details(customer_user_id=10, order_id=1)

    assert details["order"]["order_id"] == 1
    assert details["order"]["currency"] == "EUR"
    assert len(details["items"]) == 2

    assert details["items"][0]["subtotal_base"] == 200.0
    assert details["items"][1]["subtotal_base"] == 50.0
