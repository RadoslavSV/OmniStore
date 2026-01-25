from dataclasses import dataclass
from typing import Optional


@dataclass
class OrderItem:
    order_id: int
    item_id: Optional[int]
    item_name: str
    unit_price_base: float
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("OrderItem quantity must be positive")
