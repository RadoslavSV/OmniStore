from __future__ import annotations

from dataclasses import dataclass

from app.models.user import User
from app.repositories.admin_repository import AdminRepository
from app.repositories.customer_repository import CustomerRepository


@dataclass
class RoleService:
    admin_repo: AdminRepository
    customer_repo: CustomerRepository

    def enrich_user_role(self, user: User) -> User:
        """
        Returns the same user instance with role set according to Admin/Customer tables.
        Priority: ADMIN > CUSTOMER > USER
        """
        if self.admin_repo.is_admin(user.id):
            user.role = "ADMIN"
        elif self.customer_repo.is_customer(user.id):
            user.role = "CUSTOMER"
        else:
            user.role = "USER"
        return user

    def make_admin(self, user_id: int) -> None:
        self.admin_repo.make_admin(user_id, role="ADMIN")

    def make_customer(self, user_id: int, currency: str = "BGN") -> None:
        self.customer_repo.make_customer(user_id, currency=currency)
