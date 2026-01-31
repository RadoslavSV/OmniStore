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
    Real currency conversion with TTL cache.

    Primary provider (if EXCHANGERATE_HOST_KEY exists):
      - exchangerate.host /live (apilayer-compatible) -> returns quotes like {"USDEUR": 0.92}

    Fallback provider (no key needed):
      - frankfurter.app (ECB) -> returns {"rates": {"USD": ..., ...}, "base": "EUR"}

    Notes:
    - Base currency in DB is EUR.
    - Supports cross-rate conversions (from -> to).
    - Uses ONE fetch per TTL (loads all rates).
    """

    # Primary (needs key in most cases)
    live_url: str = "https://api.exchangerate.host/live"

    # Fallback (free)
    fallback_latest_url: str = "https://api.frankfurter.app/latest"

    cache_ttl_seconds: int = 6 * 3600  # 6h (safe for quotas)
    access_key: Optional[str] = None  # env EXCHANGERATE_HOST_KEY

    # Cache representation:
    # _base_currency: the base for _rates (e.g. "EUR" in fallback, or "USD" in live)
    _base_currency: str = "EUR"
    _rates: Dict[str, float] = None  # e.g. {"EUR":1.0,"USD":1.09,...} relative to _base_currency
    _cache_timestamp: float = 0.0

    def __post_init__(self):
        if self._rates is None:
            self._rates = {}

        if self.access_key is None:
            self.access_key = os.getenv("EXCHANGERATE_HOST_KEY")

    # ---------- HTTP ----------

    def _api_get(self, url: str, params: dict | None = None) -> dict:
        try:
            resp = requests.get(url, params=params or {}, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            raise CurrencyServiceError("Failed to fetch exchange rates (network/HTTP error).") from e

    # ---------- Fetchers ----------

    def _fetch_live_quotes(self) -> None:
        """
        exchangerate.host /live format:
          {"success": true, "source":"USD", "quotes":{"USDEUR":0.92, ...}}
        """
        params = {}
        if self.access_key:
            params["access_key"] = self.access_key

        data = self._api_get(self.live_url, params=params)

        # apilayer style error
        if isinstance(data, dict) and data.get("success") is False:
            err = data.get("error") or {}
            msg = err.get("info") or err.get("type") or "Exchange rate provider error"
            raise CurrencyServiceError(str(msg))

        quotes = data.get("quotes")
        source = (data.get("source") or "USD").upper()

        if not isinstance(quotes, dict) or not quotes:
            raise CurrencyServiceError("Invalid response from /live: missing 'quotes'")

        # Convert quotes (SOURCEXXX) into rates relative to SOURCE
        rates: Dict[str, float] = {source: 1.0}
        for k, v in quotes.items():
            kk = str(k).upper()
            if len(kk) == 6 and kk.startswith(source):
                cur = kk[3:]
                try:
                    rates[cur] = float(v)
                except Exception:
                    continue

        if len(rates) <= 1:
            raise CurrencyServiceError("Live provider returned no usable rates")

        self._base_currency = source
        self._rates = rates
        self._cache_timestamp = time.time()

    def _fetch_fallback_rates(self, base: str = "EUR") -> None:
        """
        frankfurter.app/latest?from=EUR
          {"amount":1.0,"base":"EUR","date":"...","rates":{"USD":1.09,...}}
        """
        base = base.upper()
        data = self._api_get(self.fallback_latest_url, params={"from": base})

        b = (data.get("base") or base).upper()
        rr = data.get("rates") or {}
        if not isinstance(rr, dict) or not rr:
            raise CurrencyServiceError("Fallback provider returned no rates")

        rates: Dict[str, float] = {b: 1.0}
        for k, v in rr.items():
            try:
                rates[str(k).upper()] = float(v)
            except Exception:
                continue

        if len(rates) <= 1:
            raise CurrencyServiceError("Fallback provider returned no usable rates")

        self._base_currency = b
        self._rates = rates
        self._cache_timestamp = time.time()

    # ---------- Cache ----------

    def _ensure_loaded(self) -> None:
        now = time.time()
        expired = (now - self._cache_timestamp) > self.cache_ttl_seconds

        if self._rates and not expired:
            return

        # Try primary first if key exists; otherwise go fallback.
        try:
            if self.access_key:
                self._fetch_live_quotes()
            else:
                self._fetch_fallback_rates(base="EUR")
        except Exception:
            # If primary fails, fallback; if fallback fails and we had old cache, keep it.
            if self._rates:
                self._cache_timestamp = now
                return
            # Last attempt: fallback
            self._fetch_fallback_rates(base="EUR")

    # ---------- Rates / Conversion ----------

    def _rate_base_to(self, currency: str) -> float:
        currency = currency.upper()
        if currency == self._base_currency:
            return 1.0

        r = self._rates.get(currency)
        if r is None:
            raise UnsupportedCurrencyError(f"Unsupported currency: {currency}")
        return float(r)

    def get_rate(self, to_currency: str, from_currency: str = "EUR") -> float:
        """
        Returns: 1 unit of from_currency expressed in to_currency.
        Cross-rate using the cached base:
          rate(from->to) = (base->to) / (base->from)
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return 1.0

        self._ensure_loaded()

        base_to_from = self._rate_base_to(from_currency)
        base_to_to = self._rate_base_to(to_currency)

        return float(base_to_to / base_to_from)

    def convert(self, amount: float, to_currency: str, from_currency: str = "EUR") -> float:
        if amount < 0:
            raise ValueError("Amount cannot be negative")

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return round(float(amount), 2)

        rate = self.get_rate(to_currency=to_currency, from_currency=from_currency)
        return round(float(amount) * rate, 2)

    def list_supported_currencies(self):
        self._ensure_loaded()
        out: Set[str] = set(self._rates.keys()) if self._rates else set()
        out.add(self._base_currency)
        return sorted({c.upper() for c in out if c})
