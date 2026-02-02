import types
import pytest

from app.services.currency_service import CurrencyService, UnsupportedCurrencyError, CurrencyServiceError, UnsupportedCurrencyError

def test_currency_service_same_currency_returns_same_amount():
    service = CurrencyService()

    amount = service.convert(100.0, from_currency="EUR", to_currency="EUR")
    assert amount == 100.0


def test_currency_service_unsupported_currency():
    service = CurrencyService()

    try:
        service.convert(100.0, from_currency="EUR", to_currency="XXX")
        assert False, "Expected UnsupportedCurrencyError"
    except UnsupportedCurrencyError:
        assert True

def test_convert_rejects_negative_amount():
    svc = CurrencyService()
    with pytest.raises(ValueError):
        svc.convert(-1, to_currency="USD", from_currency="EUR")


def test_convert_same_currency_returns_rounded_value_without_loading(monkeypatch):
    svc = CurrencyService()
    # If it tries to load rates, fail the test
    monkeypatch.setattr(svc, "_ensure_loaded", lambda: (_ for _ in ()).throw(AssertionError("Should not load")))
    assert svc.convert(10.1234, to_currency="EUR", from_currency="EUR") == 10.12


def test_get_rate_same_currency_is_1_without_loading(monkeypatch):
    svc = CurrencyService()
    monkeypatch.setattr(svc, "_ensure_loaded", lambda: (_ for _ in ()).throw(AssertionError("Should not load")))
    assert svc.get_rate("EUR", "EUR") == 1.0


def test_get_rate_cross_rate_computed_correctly(monkeypatch):
    """
    base is EUR
    EUR->USD = 1.10
    EUR->GBP = 0.80
    rate(GBP->USD) = (EUR->USD)/(EUR->GBP) = 1.10/0.80 = 1.375
    """
    svc = CurrencyService()
    svc._base_currency = "EUR"
    svc._rates = {"EUR": 1.0, "USD": 1.10, "GBP": 0.80}
    monkeypatch.setattr(svc, "_ensure_loaded", lambda: None)

    r = svc.get_rate(to_currency="USD", from_currency="GBP")
    assert r == pytest.approx(1.375)


def test_convert_uses_rate_and_rounds_to_2(monkeypatch):
    svc = CurrencyService()
    svc._base_currency = "EUR"
    svc._rates = {"EUR": 1.0, "USD": 2.0}  # EUR->USD = 2
    monkeypatch.setattr(svc, "_ensure_loaded", lambda: None)

    assert svc.convert(10, to_currency="USD", from_currency="EUR") == 20.00


def test_unsupported_currency_raises(monkeypatch):
    svc = CurrencyService()
    svc._base_currency = "EUR"
    svc._rates = {"EUR": 1.0, "USD": 1.1}
    monkeypatch.setattr(svc, "_ensure_loaded", lambda: None)

    with pytest.raises(UnsupportedCurrencyError):
        svc.get_rate("JPY", "EUR")


def test_list_supported_currencies_returns_sorted_set(monkeypatch):
    svc = CurrencyService()
    svc._base_currency = "EUR"
    svc._rates = {"EUR": 1.0, "usd": 1.1, "gbp": 0.8}
    monkeypatch.setattr(svc, "_ensure_loaded", lambda: None)

    assert svc.list_supported_currencies() == ["EUR", "GBP", "USD"]


def test_api_get_wraps_network_errors(monkeypatch):
    import app.services.currency_service as mod

    def boom(*args, **kwargs):
        raise Exception("network down")

    monkeypatch.setattr(mod.requests, "get", boom)

    svc = CurrencyService()
    with pytest.raises(CurrencyServiceError):
        svc._api_get("http://example.com")


def test_fetch_fallback_rates_parses_response(monkeypatch):
    svc = CurrencyService()

    def fake_api_get(url, params=None):
        assert "frankfurter" in url
        assert params["from"] == "EUR"
        return {"base": "EUR", "rates": {"USD": 1.2, "GBP": 0.9}}

    monkeypatch.setattr(svc, "_api_get", fake_api_get)

    svc._fetch_fallback_rates(base="EUR")

    assert svc._base_currency == "EUR"
    assert svc._rates["EUR"] == 1.0
    assert svc._rates["USD"] == 1.2
    assert svc._rates["GBP"] == 0.9


def test_fetch_live_quotes_parses_quotes(monkeypatch):
    svc = CurrencyService(access_key="x")

    def fake_api_get(url, params=None):
        assert "live" in url
        return {
            "success": True,
            "source": "USD",
            "quotes": {"USDEUR": 0.9, "USDGBP": 0.8},
        }

    monkeypatch.setattr(svc, "_api_get", fake_api_get)
    svc._fetch_live_quotes()

    assert svc._base_currency == "USD"
    assert svc._rates["USD"] == 1.0
    assert svc._rates["EUR"] == 0.9
    assert svc._rates["GBP"] == 0.8


def test_ensure_loaded_uses_fallback_when_no_key(monkeypatch):
    svc = CurrencyService(access_key=None)
    called = {"fallback": 0, "live": 0}

    monkeypatch.setattr(svc, "_fetch_live_quotes", lambda: called.__setitem__("live", called["live"] + 1))
    monkeypatch.setattr(svc, "_fetch_fallback_rates", lambda base="EUR": called.__setitem__("fallback", called["fallback"] + 1))

    svc._rates = {}
    svc._cache_timestamp = 0.0
    svc.cache_ttl_seconds = 0  # force expired

    svc._ensure_loaded()
    assert called["live"] == 0
    assert called["fallback"] == 1


def test_ensure_loaded_keeps_old_cache_if_primary_fails(monkeypatch):
    svc = CurrencyService(access_key="x")
    svc._rates = {"EUR": 1.0, "USD": 1.1}
    svc._base_currency = "EUR"
    svc._cache_timestamp = 0.0
    svc.cache_ttl_seconds = 0  # force refresh

    def fail_live():
        raise CurrencyServiceError("primary fail")

    monkeypatch.setattr(svc, "_fetch_live_quotes", fail_live)
    monkeypatch.setattr(svc, "_fetch_fallback_rates", lambda base="EUR": (_ for _ in ()).throw(AssertionError("Should not nuke old cache")))

    svc._ensure_loaded()

    # Still has the old cache
    assert svc._rates["USD"] == 1.1
