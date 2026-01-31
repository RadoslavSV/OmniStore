from __future__ import annotations
import sqlite3
from typing import Tuple

from app.services.auth_service import (
    EmailAlreadyExistsError,
    UsernameAlreadyExistsError,
    InvalidCredentialsError,
)
from app.services.cart_service import (
    CartError,
    ItemNotFoundError,
    InvalidQuantityError,
)
from app.services.checkout_service import (
    CheckoutError,
    EmptyCartError,
)
from app.services.order_history_service import (
    OrderHistoryError,
    OrderNotFoundError,
)
from app.services.currency_service import (
    CurrencyServiceError,
    UnsupportedCurrencyError,
)

# Facade-level error (we created it in store_app_service.py)
from app.presentation.app_exceptions import AppError


def map_exception(exc: Exception) -> Tuple[str, str]:
    """
    Maps internal exceptions to (code, message) suitable for UI.
    Keep messages short and user-friendly.
    """
    # ---- Facade ----
    if isinstance(exc, AppError):
        return "APP_ERROR", str(exc) or "Application error"

    # ---- Auth ----
    if isinstance(exc, EmailAlreadyExistsError):
        return "EMAIL_EXISTS", "Email is already registered"
    if isinstance(exc, UsernameAlreadyExistsError):
        return "USERNAME_EXISTS", "Username is already taken"
    if isinstance(exc, InvalidCredentialsError):
        return "INVALID_CREDENTIALS", "Invalid email or password"

    # ---- Cart ----
    if isinstance(exc, ItemNotFoundError):
        return "ITEM_NOT_FOUND", "Item not found"
    if isinstance(exc, InvalidQuantityError):
        return "INVALID_QUANTITY", "Quantity must be a positive number"
    if isinstance(exc, CartError):
        return "CART_ERROR", "Cart operation failed"

    # ---- Checkout ----
    if isinstance(exc, EmptyCartError):
        return "EMPTY_CART", "Your cart is empty"
    if isinstance(exc, CheckoutError):
        return "CHECKOUT_ERROR", "Checkout failed"

    # ---- Orders ----
    if isinstance(exc, OrderNotFoundError):
        return "ORDER_NOT_FOUND", "Order not found"
    if isinstance(exc, OrderHistoryError):
        return "ORDER_ERROR", "Order operation failed"

    # ---- Currency ----
    # (We will keep these mostly hidden until final testing)
    if isinstance(exc, UnsupportedCurrencyError):
        return "UNSUPPORTED_CURRENCY", "Unsupported currency"
    if isinstance(exc, CurrencyServiceError):
        return "CURRENCY_ERROR", "Currency service unavailable"

    # ---- Generic / DB / Validation ----
    if isinstance(exc, ValueError):
        return "VALIDATION_ERROR", str(exc) or "Invalid input"
    if isinstance(exc, sqlite3.IntegrityError):
        return "DB_INTEGRITY", "Database constraint error (duplicate or invalid data)"
    
    # ---- Fallback ----
    return "UNKNOWN_ERROR", "Unexpected error occurred"
