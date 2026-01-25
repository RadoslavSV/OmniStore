from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from app.repositories.order_repository import OrderRepository
from app.repositories.order_item_repository import OrderItemRepository


class OrderHistoryError(Exception):
    pass


class OrderNotFoundError(OrderHistoryError):
    pass


@dataclass
class OrderHistoryService:
    order_repo: OrderRepository
    order_item_repo: OrderItemRepository

    def list_orders(self, customer_user_id: int, limit: int = 50) -> List[Dict]:
        """
        Returns list of orders for customer, UI-friendly dicts.
        """
        orders = self.order_repo.list_for_customer(customer_user_id, limit=limit)
        return [
            {
                "order_id": o.id,
                "created_at": o.created_at,
                "status": o.status,
                "total_base": o.total_base,  # EUR snapshot
                "currency": "EUR",
            }
            for o in orders
        ]

    def get_order_details(self, customer_user_id: int, order_id: int) -> Dict:
        """
        Returns order + items for a specific order_id.
        Ensures the order belongs to the customer.
        """
        order = self.order_repo.get_by_id(order_id)
        if order is None or order.customer_user_id != customer_user_id:
            raise OrderNotFoundError("Order not found")

        items = self.order_item_repo.list_for_order(order_id)

        return {
            "order": {
                "order_id": order.id,
                "created_at": order.created_at,
                "status": order.status,
                "total_base": order.total_base,
                "currency": "EUR",
            },
            "items": [
                {
                    "item_id": oi.item_id,
                    "item_name": oi.item_name,
                    "unit_price_base": oi.unit_price_base,
                    "quantity": oi.quantity,
                    "subtotal_base": round(oi.unit_price_base * oi.quantity, 2),
                    "currency": "EUR",
                }
                for oi in items
            ],
        }
