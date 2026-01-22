from dataclasses import dataclass
from typing import Optional


@dataclass
class Cart:
    """
    Domain model corresponding 1:1 to the DB table Cart.
    """

    id: Optional[int]
    customer_user_id: int
