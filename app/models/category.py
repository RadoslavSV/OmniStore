from dataclasses import dataclass
from typing import Optional


@dataclass
class Category:
    """
    Domain model representing a product category.
    """

    id: Optional[int]
    name: str

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Category name cannot be empty")

    def __repr__(self) -> str:
        return f"Category(id={self.id}, name='{self.name}')"
