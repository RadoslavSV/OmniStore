from dataclasses import dataclass
from typing import Optional

from app.models.product import Dimensions


@dataclass
class Item:
    """
    Domain model corresponding 1:1 to the DB table Item.
    """

    id: Optional[int]
    admin_user_id: int

    name: str
    description: str

    dimensions: Dimensions
    weight: float
    price: float

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Item name cannot be empty")
        if not self.description or not self.description.strip():
            raise ValueError("Item description cannot be empty")
        if self.price < 0:
            raise ValueError("Item price cannot be negative")
        if self.weight < 0:
            raise ValueError("Item weight cannot be negative")
        if self.dimensions.length <= 0 or self.dimensions.width <= 0 or self.dimensions.height <= 0:
            raise ValueError("Item dimensions must be positive")
