from dataclasses import dataclass, field
from typing import Optional, List


@dataclass(frozen=True)
class Dimensions:
    """
    Value object representing physical dimensions of a product.
    Units are assumed to be centimeters.
    """

    length: float
    width: float
    height: float

    def volume(self) -> float:
        return self.length * self.width * self.height


@dataclass
class Product:
    """
    Domain model representing a product in the virtual store.
    """

    id: Optional[int]
    name: str
    description: str
    base_price: float
    category_id: Optional[int]

    dimensions: Dimensions
    image_paths: List[str] = field(default_factory=list)

    def __post_init__(self):
        if self.base_price < 0:
            raise ValueError("Product price cannot be negative")

    def has_3d_representation(self) -> bool:
        """
        Product can be visualized in 3D if it has valid dimensions.
        """
        return (
            self.dimensions.length > 0
            and self.dimensions.width > 0
            and self.dimensions.height > 0
        )

    def __repr__(self) -> str:
        return (
            f"Product(id={self.id}, "
            f"name='{self.name}', "
            f"price={self.base_price}, "
            f"category_id={self.category_id})"
        )
