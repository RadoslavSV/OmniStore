from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Set
import os
import time
import requests


class CurrencyServiceError(Exception):
    pass


class UnsupportedCurrencyError(CurrencyServiceError):
    pass


@dataclass
class CurrencyService:
    """
    Currency conversion service using exchangerate.host /live (apilayer).

    IMPORTANT DEV behavior:
    - If OMNISTORE_ENABLE_CURRENCY_API != "1" -> NO HTTP calls.
    - In DEV mode we use a small mock table (base EUR) so UI can be tested realistically.
    - When API is enabled -> uses /live quotes with TTL cache.
    """

    live_url: str = "https://api.exchangerate.host/live"
    cache_ttl_seconds: int = 6 * 3600  # 6 hours by default
    access_key: Optional[str] = None  # env EXCHANGERATE_HOST_KEY

    # API data (source usually USD)
    _source_currency: str = "USD"
    _quotes_cache: Dict[str, float] = None  # e.g. {"USDEUR": 0.92, ...}
    _cache_timestamp: float = 0.0

    # DEV mock rates (base EUR)
    _dev_base: str = "EUR"
    _dev_rates_from_eur: Dict[str, float] = None

    def __post_init__(self):
        if self._quotes_cache is None:
            self._quotes_cache = {}

        # Small stable dev table (rough rates; enough to visually confirm conversion works)
        if self._dev_rates_from_eur is None:
            self._dev_rates_from_eur = {
                "EUR": 1.0,
                "USD": 1.10,
                "GBP": 0.86,
                "BGN": 1.95583,
                "RON": 4.95,
                "TRY": 35.0,
                "CHF": 0.95,
                "JPY": 165.0,
                "CAD": 1.48,
                "AUD": 1.65,
            }

        # Hard switch: API disabled by default during development
        enable_api = os.getenv("OMNISTORE_ENABLE_CURRENCY_API", "0") == "1"

        if not enable_api:
            # Force-disable API calls even if a key exists in env
            self.access_key = None
        else:
            if self.access_key is None:
                self.access_key = os.getenv("EXCHANGERATE_HOST_KEY")

    # ---------- Internal (API mode) ----------

    def _api_get(self, url: str, params: dict) -> dict:
        try:
            resp = requests.get(url, params=params, timeout=8)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            raise CurrencyServiceError(f"HTTP error: {e}") from e
        except Exception as e:
            raise CurrencyServiceError("Failed to fetch exchange rates (network/HTTP error).") from e

    def _fetch_all_quotes_live(self) -> None:
        params = {}
        if self.access_key:
            params["access_key"] = self.access_key

        data = self._api_get(self.live_url, params)

        if isinstance(data, dict) and data.get("success") is False:
            err = data.get("error") or {}
            msg = err.get("info") or err.get("type") or str(data)
            raise CurrencyServiceError(f"ExchangeRate.host error: {msg}")

        quotes = data.get("quotes")
        source = data.get("source") or self._source_currency

        if not isinstance(quotes, dict) or not quotes:
            raise CurrencyServiceError("Invalid response from /live: missing 'quotes'")

        self._source_currency = str(source).upper()
        self._quotes_cache = {str(k).upper(): float(v) for k, v in quotes.items()}
        self._cache_timestamp = time.time()

    def _ensure_loaded(self) -> None:
        now = time.time()
        expired = (now - self._cache_timestamp) > self.cache_ttl_seconds

        # No key -> never call external API
        if not self.access_key:
            return

        if self._quotes_cache and not expired:
            return

        try:
            self._fetch_all_quotes_live()
        except CurrencyServiceError:
            # If we already have some cache, keep it
            if self._quotes_cache:
                self._cache_timestamp = now  # prevent tight re-fetch loops
                return
            self._quotes_cache = {}
            self._cache_timestamp = now

    def _rate_source_to(self, currency: str) -> float:
        currency = currency.upper()
        if currency == self._source_currency:
            return 1.0

        key = f"{self._source_currency}{currency}"
        rate = self._quotes_cache.get(key)
        if rate is None:
            raise UnsupportedCurrencyError(f"Unsupported currency: {currency}")
        return float(rate)

    # ---------- Internal (DEV mock mode) ----------

    def _dev_rate(self, to_currency: str, from_currency: str) -> float:
        """
        Returns: 1 unit of from_currency expressed in to_currency using DEV mock table (base EUR).
        """
        to_currency = to_currency.upper()
        from_currency = from_currency.upper()

        rates = self._dev_rates_from_eur or {}
        if to_currency not in rates or from_currency not in rates:
            raise UnsupportedCurrencyError(f"Unsupported currency: {to_currency} or {from_currency}")

        # rate(EUR->X) = rates[X]
        # rate(from->to) = (EUR->to) / (EUR->from)
        return float(rates[to_currency] / rates[from_currency])

    # ---------- Public API ----------

    def get_rate(self, to_currency: str, from_currency: str = "EUR") -> float:
        """
        Returns: 1 unit of from_currency expressed in to_currency.
        - DEV mode (API OFF): uses mock table.
        - API mode (API ON): cross-rate via SOURCE currency.
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return 1.0

        # DEV mode (no API)
        if not self.access_key:
            return self._dev_rate(to_currency=to_currency, from_currency=from_currency)

        # API mode
        self._ensure_loaded()
        if not self._quotes_cache:
            # Best-effort fallback
            return 1.0

        s_to_from = self._rate_source_to(from_currency)
        s_to_to = self._rate_source_to(to_currency)
        return float(s_to_to / s_to_from)

    def convert(self, amount: float, to_currency: str, from_currency: str = "EUR") -> float:
        if amount < 0:
            raise ValueError("Amount cannot be negative")

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return round(amount, 2)

        rate = self.get_rate(to_currency=to_currency, from_currency=from_currency)
        return round(amount * rate, 2)

    def list_supported_currencies(self):
        """
        Returns currencies that the service can work with.
        - DEV mode: returns mock table keys.
        - API mode: returns currencies from current cache (triggers fetch if needed).
        """
        # DEV mode
        if not self.access_key:
            return sorted(set((self._dev_rates_from_eur or {}).keys()))

        # API mode
        self._ensure_loaded()

        src = self._source_currency
        out: Set[str] = {src}

        for k in self._quotes_cache.keys():
            k = str(k).upper()
            if k.startswith(src) and len(k) == 6:
                out.add(k[3:])

        # Ensure EUR present for your app baseline
        out.add("EUR")
        return sorted(out)
