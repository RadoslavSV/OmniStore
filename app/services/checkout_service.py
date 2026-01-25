from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.repositories.cart_repository import CartRepository
from app.repositories.item_cart_repository import ItemCartRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.order_item_repository import OrderItemRepository
from app.models.order_item import OrderItem


class CheckoutError(Exception):
    pass


class EmptyCartError(CheckoutError):
    pass


@dataclass
class CheckoutService:
    cart_repo: CartRepository
    item_cart_repo: ItemCartRepository
    item_repo: ItemRepository
    order_repo: OrderRepository
    order_item_repo: OrderItemRepository

    base_currency: str = "EUR"

    def checkout(self, customer_user_id: int) -> int:
        """
        Creates an Order + OrderItems snapshot from the customer's cart, then clears the cart.
        Prices are snapshot-ed in EUR (base currency).
        """
        cart = self.cart_repo.get_or_create_for_customer(customer_user_id)
        cart_items = self.item_cart_repo.list_items(cart.id)

        if not cart_items:
            raise EmptyCartError("Cart is empty")

        created_at = datetime.now(timezone.utc).isoformat()
        order_id = self.order_repo.create(customer_user_id, created_at, status="CREATED", total_base=0.0)

        total_base = 0.0
        for ci in cart_items:
            item = self.item_repo.get_by_id(ci.item_id)
            if item is None:
                # If item vanished, just skip it (or you can raise)
                continue

            unit_price = float(item.price)
            total_base += unit_price * ci.quantity

            self.order_item_repo.add(
                OrderItem(
                    order_id=order_id,
                    item_id=item.id,
                    item_name=item.name,          # snapshot
                    unit_price_base=unit_price,   # snapshot in EUR
                    quantity=ci.quantity,
                )
            )

        self.order_repo.update_total_base(order_id, round(total_base, 2))

        # Clear cart after successful order creation
        # (no need to delete cart row; just items)
        self._clear_cart(cart.id)

        return order_id

    def _clear_cart(self, cart_id: int) -> None:
        # minimal, local cleanup without asking you to add new repo methods
        # (keeps your "don't add extra stuff now" request)
        import sqlite3
        from app.db.connection import get_connection

        conn = get_connection()
        try:
            conn.execute("DELETE FROM Item_Cart WHERE CartID = ?", (cart_id,))
            conn.commit()
        finally:
            conn.close()
