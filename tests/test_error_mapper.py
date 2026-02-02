import sqlite3
import pytest

from app.presentation.error_mapper import map_exception
from app.presentation.app_exceptions import AppError

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


def test_map_exception_app_error():
    code, msg = map_exception(AppError("Item not found"))
    assert code == "APP_ERROR"
    assert msg == "Item not found"


def test_map_exception_email_exists():
    code, msg = map_exception(EmailAlreadyExistsError("x"))
    assert code == "EMAIL_EXISTS"
    assert msg == "Email is already registered"


def test_map_exception_username_exists():
    code, msg = map_exception(UsernameAlreadyExistsError("x"))
    assert code == "USERNAME_EXISTS"
    assert msg == "Username is already taken"


def test_map_exception_invalid_credentials():
    code, msg = map_exception(InvalidCredentialsError("x"))
    assert code == "INVALID_CREDENTIALS"
    assert msg == "Invalid email or password"


def test_map_exception_item_not_found():
    code, msg = map_exception(ItemNotFoundError("x"))
    assert code == "ITEM_NOT_FOUND"
    assert msg == "Item not found"


def test_map_exception_invalid_quantity():
    code, msg = map_exception(InvalidQuantityError("x"))
    assert code == "INVALID_QUANTITY"
    assert msg == "Quantity must be a positive number"


def test_map_exception_cart_error_generic():
    code, msg = map_exception(CartError("x"))
    assert code == "CART_ERROR"
    assert msg == "Cart operation failed"


def test_map_exception_empty_cart():
    code, msg = map_exception(EmptyCartError("x"))
    assert code == "EMPTY_CART"
    assert msg == "Your cart is empty"


def test_map_exception_checkout_error_generic():
    code, msg = map_exception(CheckoutError("x"))
    assert code == "CHECKOUT_ERROR"
    assert msg == "Checkout failed"


def test_map_exception_order_not_found():
    code, msg = map_exception(OrderNotFoundError("x"))
    assert code == "ORDER_NOT_FOUND"
    assert msg == "Order not found"


def test_map_exception_order_history_error_generic():
    code, msg = map_exception(OrderHistoryError("x"))
    assert code == "ORDER_ERROR"
    assert msg == "Order operation failed"


def test_map_exception_unsupported_currency():
    code, msg = map_exception(UnsupportedCurrencyError("x"))
    assert code == "UNSUPPORTED_CURRENCY"
    assert msg == "Unsupported currency"


def test_map_exception_currency_service_error():
    code, msg = map_exception(CurrencyServiceError("x"))
    assert code == "CURRENCY_ERROR"
    assert msg == "Currency service unavailable"


def test_map_exception_value_error_uses_message():
    code, msg = map_exception(ValueError("Bad input"))
    assert code == "VALIDATION_ERROR"
    assert msg == "Bad input"


def test_map_exception_sqlite_integrity_error():
    code, msg = map_exception(sqlite3.IntegrityError("x"))
    assert code == "DB_INTEGRITY"
    assert msg == "Database constraint error (duplicate or invalid data)"


def test_map_exception_unknown_fallback():
    class Weird(Exception):
        pass

    code, msg = map_exception(Weird("x"))
    assert code == "UNKNOWN_ERROR"
    assert msg == "Unexpected error occurred"
