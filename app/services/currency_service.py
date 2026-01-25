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
    Goals:
    - ONE request per TTL (fetch ALL quotes, no per-currency fetch) -> protects quota & avoids rate-limit bursts
    - In-memory cache with TTL
    - Cross-rate conversion supported (from -> to) via SOURCE currency (usually USD)
    - Graceful fallback if missing key or temporary rate-limit (use cached rates if available)
    """

    live_url: str = "https://api.exchangerate.host/live"
    cache_ttl_seconds: int = 6 * 3600  # 6 hours by default (better for 100 requests/month)
    access_key: Optional[str] = None  # or env EXCHANGERATE_HOST_KEY

    _source_currency: str = "USD"
    _quotes_cache: Dict[str, float] = None  # e.g. {"USDEUR": 0.92, "USDGBP": 0.79, ...}
    _cache_timestamp: float = 0.0

    def __post_init__(self):
        if self._quotes_cache is None:
            self._quotes_cache = {}
        # Hard switch: API disabled by default during development
        _enable = os.getenv("OMNISTORE_ENABLE_CURRENCY_API", "0") == "1"

        if not _enable:
            # Force-disable API calls even if a key exists in env
            self.access_key = None
        else:
            if self.access_key is None:
                self.access_key = os.getenv("EXCHANGERATE_HOST_KEY")


    # ---------- Internal ----------

    def _api_get(self, url: str, params: dict) -> dict:
        try:
            resp = requests.get(url, params=params, timeout=8)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            # Special-case 429: rate limit. We'll handle gracefully in _ensure_loaded().
            raise CurrencyServiceError(f"HTTP error: {e}") from e
        except Exception as e:
            raise CurrencyServiceError("Failed to fetch exchange rates (network/HTTP error).") from e

    def _fetch_all_quotes_live(self) -> None:
        """
        Fetches ALL quotes in one call (no 'currencies' param) to avoid extra calls.
        """
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
        """
        Loads cache if empty/expired.
        If rate-limited (429), keeps existing cache (if any) and continues.
        If no cache at all, does graceful fallback (no conversion).
        """
        now = time.time()
        expired = (now - self._cache_timestamp) > self.cache_ttl_seconds

        # No key -> never call external API
        if not self.access_key:
            if self._quotes_cache is None:
                self._quotes_cache = {}
            self._cache_timestamp = now
            return

        if self._quotes_cache and not expired:
            return

        try:
            self._fetch_all_quotes_live()
        except CurrencyServiceError:
            # If we already have some cache, keep it (best-effort)
            if self._quotes_cache:
                self._cache_timestamp = now  # prevent tight re-fetch loops
                return
            # No cache -> cannot convert; leave empty and let public methods fallback
            self._quotes_cache = {}
            self._cache_timestamp = now

    def _rate_source_to(self, currency: str) -> float:
        """
        Returns rate: 1 SOURCE = X CURRENCY
        """
        currency = currency.upper()
        if currency == self._source_currency:
            return 1.0

        key = f"{self._source_currency}{currency}"
        rate = self._quotes_cache.get(key)
        if rate is None:
            raise UnsupportedCurrencyError(f"Unsupported currency: {currency}")
        return float(rate)

    # ---------- Public API ----------

    def get_rate(self, to_currency: str, from_currency: str = "EUR") -> float:
        """
        Returns: 1 unit of from_currency expressed in to_currency.
        Cross-rate via SOURCE currency:
          rate(from->to) = (SOURCE->to) / (SOURCE->from)
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return 1.0

        self._ensure_loaded()

        # If cache is empty (no key / rate-limited with no cache), fallback 1:1
        if not self._quotes_cache:
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

        # No key -> no external calls -> graceful fallback
        if not self.access_key:
            return round(amount, 2)

        rate = self.get_rate(to_currency=to_currency, from_currency=from_currency)
        return round(amount * rate, 2)

    def list_supported_currencies(self):
        """
        Returns currencies from the current cache.
        Will trigger one fetch if cache empty/expired (and key exists).
        """
        self._ensure_loaded()

        src = self._source_currency
        out: Set[str] = {src}

        for k in self._quotes_cache.keys():
            k = str(k).upper()
            if k.startswith(src) and len(k) == 6:
                out.add(k[3:])

        return sorted(out)
