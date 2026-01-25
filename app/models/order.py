from dataclasses import dataclass
from typing import Optional


@dataclass
class Order:
    id: Optional[int]
    customer_user_id: int
    created_at: str
    status: str
    total_base: float
