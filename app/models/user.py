from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """
    Domain model representing a system user.
    This class contains NO database or UI logic.
    """

    id: Optional[int]
    username: str
    email: str
    password_hash: str
    role: str = "USER"  # USER or ADMIN

    def is_admin(self) -> bool:
        return self.role.upper() == "ADMIN"

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, "
            f"username='{self.username}', "
            f"email='{self.email}', "
            f"role='{self.role}')"
        )
