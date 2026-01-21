from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.utils.security import hash_password, verify_password


# --------- Domain/service-level exceptions (за UI съобщения) ---------

class AuthError(Exception):
    """Base class for auth-related errors."""


class EmailAlreadyExistsError(AuthError):
    pass


class UsernameAlreadyExistsError(AuthError):
    pass


class InvalidCredentialsError(AuthError):
    pass


class WeakPasswordError(AuthError):
    pass


# --------- Service ---------

@dataclass
class AuthService:
    user_repo: UserRepository

    def register(self, username: str, email: str, name: str, password: str) -> User:
        username = (username or "").strip()
        email = (email or "").strip()
        name = (name or "").strip()

        if not username:
            raise ValueError("Username is required")
        if not email:
            raise ValueError("Email is required")
        if not name:
            raise ValueError("Name is required")

        # basic password policy (можеш да я направиш по-строга по-късно)
        if not password or len(password) < 6:
            raise WeakPasswordError("Password must be at least 6 characters long")

        if self.user_repo.exists_email(email):
            raise EmailAlreadyExistsError("Email is already registered")

        if self.user_repo.exists_username(username):
            raise UsernameAlreadyExistsError("Username is already taken")

        pw_hash = hash_password(password)
        user_id = self.user_repo.create(
            username=username,
            email=email,
            password_hash=pw_hash,
            name=name,
        )

        created = self.user_repo.get_by_id(user_id)
        # created няма как да е None, но пазим sanity check:
        if created is None:
            raise AuthError("User creation failed unexpectedly")

        return created

    def login(self, email: str, password: str) -> User:
        email = (email or "").strip()

        if not email or not password:
            raise InvalidCredentialsError("Invalid email or password")

        user = self.user_repo.get_by_email(email)
        if user is None:
            raise InvalidCredentialsError("Invalid email or password")

        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        return user
