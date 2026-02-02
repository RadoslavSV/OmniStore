import pytest

from app.services.store_app_service import StoreAppService
from app.presentation.app_exceptions import AppError


class Dummy:
    """Generic stub object for repo/service fields in StoreAppService."""
    pass


def make_app():
    # Build StoreAppService with dummy deps (won't be used in run() tests)
    return StoreAppService(
        user_repo=Dummy(),
        admin_repo=Dummy(),
        customer_repo=Dummy(),
        item_repo=Dummy(),
        category_repo=Dummy(),
        item_category_repo=Dummy(),
        picture_repo=Dummy(),
        cart_repo=Dummy(),
        item_cart_repo=Dummy(),
        favorites_repo=Dummy(),
        history_repo=Dummy(),
        order_repo=Dummy(),
        order_item_repo=Dummy(),
        auth=Dummy(),
        roles=Dummy(),
        cart=Dummy(),
        checkout=Dummy(),
        order_history=Dummy(),
        favorites=Dummy(),
        history=Dummy(),
        currency=Dummy(),
        base_currency="EUR",
    )


def test_run_success_wraps_value_in_app_result():
    app = make_app()

    def op():
        return 123

    res = app.run(op)
    assert res.ok is True
    assert res.data == 123
    assert res.error is None


def test_run_maps_app_error_to_failure():
    app = make_app()

    def op():
        raise AppError("Item not found")

    res = app.run(op)
    assert res.ok is False
    assert res.data is None
    assert res.error is not None
    assert res.error.code == "APP_ERROR"
    assert res.error.message == "Item not found"


def test_run_maps_value_error_to_validation_error():
    app = make_app()

    def op():
        raise ValueError("Bad input")

    res = app.run(op)
    assert res.ok is False
    assert res.error.code == "VALIDATION_ERROR"
    assert res.error.message == "Bad input"


def test_run_passes_args_and_kwargs():
    app = make_app()

    def op(a, b=0):
        return a + b

    res = app.run(op, 2, b=3)
    assert res.ok is True
    assert res.data == 5
