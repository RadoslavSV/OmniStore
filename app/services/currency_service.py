from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Iterable
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
    Currency conversion service using https://exchangerate.host (LIVE endpoint).
    - Handles modern response format with `quotes`
    - Handles success:false with error info
    - Simple in-memory caching
    - Supports conversion between ANY two currencies via cross-rate
    """

    base_url: str = "https://api.exchangerate.host/live"
    cache_ttl_seconds: int = 3600  # 1 hour
    access_key: Optional[str] = None  # set via constructor or env EXCHANGERATE_HOST_KEY

    _quotes_cache: Dict[str, float] = None   
    _cache_timestamp: float = 0.0
    _source_currency: str = "USD"  # live endpoint default source is usually USD :contentReference[oaicite:1]{index=1}

    def __post_init__(self):
        if self._quotes_cache is None:
            self._quotes_cache = {}

        if self.access_key is None:
            self.access_key = os.getenv("EXCHANGERATE_HOST_KEY")

    # ---------- Internal ----------

    def _fetch_quotes(self, currencies: Optional[Iterable[str]] = None) -> None:
        params = {}
        if self.access_key:
            params["access_key"] = self.access_key

        # currencies param reduces payload; ok to omit (returns many)
        if currencies:
            params["currencies"] = ",".join(sorted({c.upper() for c in currencies}))

        try:
            resp = requests.get(self.base_url, params=params, timeout=8)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            raise CurrencyServiceError("Failed to fetch exchange rates (network/HTTP error).") from e

        # If API returns success:false, surface the reason
        if isinstance(data, dict) and data.get("success") is False:
            err = data.get("error") or {}
            msg = err.get("info") or err.get("type") or str(data)
            raise CurrencyServiceError(f"ExchangeRate.host error: {msg}")

        # Parse quotes format
        quotes = data.get("quotes")
        source = data.get("source") or self._source_currency

        if not isinstance(quotes, dict) or not quotes:
            # Some deployments still return `rates`; handle just in case
            rates = data.get("rates")
            base = data.get("base") or source
            if isinstance(rates, dict) and rates:
                # Convert rates -> quotes-like relative to base
                # base->XXX
                self._source_currency = base.upper()
                self._quotes_cache = {f"{self._source_currency}{k.upper()}": float(v) for k, v in rates.items()}
                self._cache_timestamp = time.time()
                return

            raise CurrencyServiceError("Invalid response: neither 'quotes' nor 'rates' found.")

        self._source_currency = str(source).upper()
        self._quotes_cache = {str(k).upper(): float(v) for k, v in quotes.items()}
        self._cache_timestamp = time.time()

    def _ensure_loaded(self, needed: Optional[Iterable[str]] = None) -> None:
        expired = (time.time() - self._cache_timestamp) > self.cache_ttl_seconds
        if not self._quotes_cache or expired:
            # Make sure we include the needed currencies for cross-rate conversion
            self._fetch_quotes(currencies=needed)

    def _usd_to(self, currency: str) -> float:
        currency = currency.upper()
        if currency == self._source_currency:
            return 1.0

        key = f"{self._source_currency}{currency}"
        rate = self._quotes_cache.get(key)
        if rate is None:
            raise UnsupportedCurrencyError(f"Unsupported currency: {currency}")
        return float(rate)

    # ---------- Public API ----------

    def convert(self, amount: float, to_currency: str, from_currency: str = "EUR") -> float:
        """
        Convert amount from one currency to another via cross-rate.
        Default from_currency = EUR (както ти е удобно за магазина).
        """
        if amount < 0:
            raise ValueError("Amount cannot be negative")

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # ensure we have both currencies in cache (for cross-rate)
        self._ensure_loaded(needed=[from_currency, to_currency])

        if from_currency == to_currency:
            return round(amount, 2)

        # quotes are relative to source_currency (usually USD)
        # amount_in_source = amount / (source->from)
        # result = amount_in_source * (source->to)
        rate_source_to_from = self._usd_to(from_currency)
        rate_source_to_to = self._usd_to(to_currency)

        amount_in_source = amount / rate_source_to_from
        result = amount_in_source * rate_source_to_to
        return round(result, 2)

    def get_rate(self, to_currency: str, from_currency: str = "EUR") -> float:
        """
        Returns 1 unit of from_currency expressed in to_currency.
        """
        return self.convert(1.0, to_currency=to_currency, from_currency=from_currency)

    def list_supported_currencies(self):
        self._ensure_loaded()
        # extract suffix currencies from e.g. "USDXXX"
        src = self._source_currency
        out = set()
        for k in self._quotes_cache.keys():
            if k.startswith(src) and len(k) == 6:
                out.add(k[3:])
        out.add(src)
        return sorted(out)
