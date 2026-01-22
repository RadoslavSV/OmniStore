from dataclasses import dataclass


@dataclass
class CartItem:
    """
    Domain model for an item in a cart (maps to Item_Cart table).
    """

    cart_id: int
    item_id: int
    quantity: int

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError("CartItem quantity must be positive")
