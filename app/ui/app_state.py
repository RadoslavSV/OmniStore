from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class AppUserSession:
    user_id: int
    username: str
    email: str
    role: str  # "GUEST" | "CUSTOMER" | "ADMIN"
    currency: str = "EUR"


@dataclass
class AppState:
    session: Optional[AppUserSession] = None

    @property
    def is_logged_in(self) -> bool:
        return self.session is not None and self.session.role != "GUEST"

    @property
    def role(self) -> str:
        return self.session.role if self.session else "GUEST"

    @property
    def currency(self) -> str:
        return self.session.currency if self.session else "EUR"

    def set_guest(self) -> None:
        self.session = None

    def set_session(self, user_id: int, username: str, email: str, role: str, currency: str = "EUR") -> None:
        self.session = AppUserSession(
            user_id=user_id,
            username=username,
            email=email,
            role=role.upper(),
            currency=currency.upper() if currency else "EUR",
        )
