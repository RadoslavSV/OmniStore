from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict

from app.repositories.cart_repository import CartRepository
from app.repositories.item_cart_repository import ItemCartRepository
from app.repositories.item_repository import ItemRepository
from app.models.cart_item import CartItem


class CartError(Exception):
    pass


class ItemNotFoundError(CartError):
    pass


class InvalidQuantityError(CartError):
    pass


@dataclass
class CartService:
    cart_repo: CartRepository
    item_cart_repo: ItemCartRepository
    item_repo: ItemRepository

    # ---------- Core operations ----------

    def get_cart_for_customer(self, customer_user_id: int):
        return self.cart_repo.get_or_create_for_customer(customer_user_id)

    def add_item(self, customer_user_id: int, item_id: int, quantity: int = 1) -> None:
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be positive")

        if self.item_repo.get_by_id(item_id) is None:
            raise ItemNotFoundError(f"Item {item_id} does not exist")

        cart = self.get_cart_for_customer(customer_user_id)
        self.item_cart_repo.increment(cart.id, item_id, delta=quantity)

    def set_quantity(self, customer_user_id: int, item_id: int, quantity: int) -> None:
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be positive")

        cart = self.get_cart_for_customer(customer_user_id)
        self.item_cart_repo.upsert_quantity(cart.id, item_id, quantity)

    def remove_item(self, customer_user_id: int, item_id: int) -> None:
        cart = self.get_cart_for_customer(customer_user_id)
        self.item_cart_repo.remove_item(cart.id, item_id)

    # ---------- Read operations ----------

    def get_items(self, customer_user_id: int) -> List[CartItem]:
        cart = self.get_cart_for_customer(customer_user_id)
        return self.item_cart_repo.list_items(cart.id)

    def get_detailed_items(self, customer_user_id: int) -> List[Dict]:
        """
        Returns list of dicts:
        {
            item_id, name, price, quantity, subtotal
        }
        """
        cart = self.get_cart_for_customer(customer_user_id)
        cart_items = self.item_cart_repo.list_items(cart.id)

        result: List[Dict] = []
        for ci in cart_items:
            item = self.item_repo.get_by_id(ci.item_id)
            if item is None:
                continue  # safety: item deleted

            subtotal = item.price * ci.quantity
            result.append(
                {
                    "item_id": item.id,
                    "name": item.name,
                    "price": item.price,
                    "quantity": ci.quantity,
                    "subtotal": round(subtotal, 2),
                }
            )
        return result

    def get_total(self, customer_user_id: int) -> float:
        detailed = self.get_detailed_items(customer_user_id)
        total = sum(row["subtotal"] for row in detailed)
        return round(total, 2)

    # ---------- Maintenance rule ----------

    def remove_item_from_all_carts(self, item_id: int) -> None:
        """
        Business rule: if an item is deleted from catalog,
        it must be removed from all carts.
        """
        # delegated entirely to DB cascade via Item_Cart FK
        # this method exists for semantic completeness
        pass
