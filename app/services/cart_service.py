from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Optional

from app.repositories.cart_repository import CartRepository
from app.repositories.item_cart_repository import ItemCartRepository
from app.repositories.item_repository import ItemRepository
from app.repositories.customer_repository import CustomerRepository

from app.models.cart_item import CartItem
from app.services.service_container import currency_service  # shared singleton


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
    customer_repo: CustomerRepository

    # System base currency (prices in DB are in EUR)
    base_currency: str = "EUR"

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

    # ---------- Currency helpers ----------

    def _get_customer_currency(self, customer_user_id: int) -> str:
        cur = self.customer_repo.get_currency(customer_user_id)
        return (cur or self.base_currency).upper()

    # ---------- Read operations ----------

    def get_items(self, customer_user_id: int) -> List[CartItem]:
        cart = self.get_cart_for_customer(customer_user_id)
        return self.item_cart_repo.list_items(cart.id)

    def get_detailed_items(
        self,
        customer_user_id: int,
        display_currency: Optional[str] = None,
    ) -> List[Dict]:
        """
        Returns list of dicts ready for UI:
        {
          item_id, name,
          unit_price_base, subtotal_base,
          unit_price, subtotal,
          quantity,
          currency
        }

        - unit_price_base/subtotal_base are in EUR (base_currency)
        - unit_price/subtotal are in display_currency
        """
        cart = self.get_cart_for_customer(customer_user_id)
        cart_items = self.item_cart_repo.list_items(cart.id)

        target = (display_currency or self._get_customer_currency(customer_user_id)).upper()

        result: List[Dict] = []
        for ci in cart_items:
            item = self.item_repo.get_by_id(ci.item_id)
            if item is None:
                continue  # if item was deleted

            unit_base = float(item.price)
            subtotal_base = unit_base * ci.quantity

            api_enabled = bool(getattr(currency_service, "access_key", None))

            if (target == self.base_currency) or (not api_enabled):
                unit_disp = round(unit_base, 2)
                subtotal_disp = round(subtotal_base, 2)
                target = self.base_currency  # show EUR whilst API is turned off
            else:
                unit_disp = currency_service.convert(unit_base, to_currency=target, from_currency=self.base_currency)
                subtotal_disp = currency_service.convert(subtotal_base, to_currency=target, from_currency=self.base_currency)


            result.append(
                {
                    "item_id": item.id,
                    "name": item.name,
                    "quantity": ci.quantity,
                    "unit_price_base": round(unit_base, 2),
                    "subtotal_base": round(subtotal_base, 2),
                    "unit_price": unit_disp,
                    "subtotal": subtotal_disp,
                    "currency": target,
                }
            )

        return result

    def get_total(
        self,
        customer_user_id: int,
        display_currency: Optional[str] = None,
    ) -> Dict:
        """
        Returns:
        {
          total_base: <EUR total>,
          total: <converted total>,
          currency: <display currency>
        }
        """
        target = (display_currency or self._get_customer_currency(customer_user_id)).upper()

        detailed = self.get_detailed_items(customer_user_id, display_currency=target)
        total_base = round(sum(row["subtotal_base"] for row in detailed), 2)

        api_enabled = bool(getattr(currency_service, "access_key", None))

        if (target == self.base_currency) or (not api_enabled):
            total = total_base
            target = self.base_currency
        else:
            total = currency_service.convert(total_base, to_currency=target, from_currency=self.base_currency)

        return {"total_base": total_base, "total": total, "currency": target}
