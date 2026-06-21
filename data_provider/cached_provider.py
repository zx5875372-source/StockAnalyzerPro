from __future__ import annotations

from collections.abc import Callable

from data_provider.cache import CacheKey, ICache, MemoryCache
from data_provider.interfaces import IDataProvider, PriceHistory, ProviderDiagnostic
from models.financial_data import FinancialData


DEFAULT_TTL_SECONDS = {
    "info": 24 * 60 * 60,
    "financials": 7 * 24 * 60 * 60,
    "balance_sheet": 7 * 24 * 60 * 60,
    "cashflow": 7 * 24 * 60 * 60,
    "price_history": 24 * 60 * 60,
    "snapshot": None,
    "universe": None,
}


class CachedDataProvider(IDataProvider):
    def __init__(
        self,
        provider: IDataProvider,
        cache: ICache | None = None,
        ttl_seconds_by_data_type: dict[str, int | None] | None = None,
    ):
        self.provider = provider
        self.cache = cache or MemoryCache()
        self.ttl_seconds_by_data_type = {
            **DEFAULT_TTL_SECONDS,
            **(ttl_seconds_by_data_type or {}),
        }
        self.name = f"cached_{provider.name}"
        self._diagnostics: list[ProviderDiagnostic] = []

    def get_financial_data(self, symbol: str, as_of: str | None = None) -> FinancialData:
        key = CacheKey(
            provider=self.provider.name,
            symbol=self._normalize_symbol(symbol),
            data_type="financials",
            period=f"annual_as_of_{as_of}" if as_of else "annual",
        )
        return self._get_or_fetch(
            key,
            symbol=key.symbol,
            fetch=lambda: self.provider.get_financial_data(symbol, as_of=as_of),
        )

    def get_price_history(self, symbol: str, start: str, end: str) -> PriceHistory:
        key = CacheKey(
            provider=self.provider.name,
            symbol=self._normalize_symbol(symbol),
            data_type="price_history",
            period="daily",
            start_date=start,
            end_date=end,
        )
        return self._get_or_fetch(
            key,
            symbol=key.symbol,
            fetch=lambda: self.provider.get_price_history(symbol, start, end),
        )

    def get_universe(self, universe_id: str) -> list[str]:
        key = CacheKey(
            provider=self.provider.name,
            symbol=universe_id,
            data_type="universe",
            period="none",
        )
        return self._get_or_fetch(
            key,
            symbol=universe_id,
            fetch=lambda: self.provider.get_universe(universe_id),
        )

    def diagnostics(self) -> list[ProviderDiagnostic]:
        provider_diagnostics = self.provider.diagnostics()
        return list(self._diagnostics) + list(provider_diagnostics)

    def _get_or_fetch(self, key: CacheKey, symbol: str | None, fetch: Callable):
        if self._is_expired(key):
            self._record("cache_expired", key, symbol)

        cached = self.cache.get(key)
        if cached is not None:
            self._record("cache_hit", key, symbol)
            return cached

        self._record("cache_miss", key, symbol)
        self._record("provider_called", key, symbol)
        value = fetch()
        self.cache.set(key, value, ttl_seconds=self._ttl_seconds(key.data_type))
        return value

    def _ttl_seconds(self, data_type: str) -> int | None:
        return self.ttl_seconds_by_data_type.get(data_type)

    def _is_expired(self, key: CacheKey) -> bool:
        checker = getattr(self.cache, "is_expired", None)
        if checker is None:
            return False
        return bool(checker(key))

    def _record(self, event: str, key: CacheKey, symbol: str | None) -> None:
        self._diagnostics.append(
            ProviderDiagnostic(
                provider=self.name,
                severity="info",
                symbol=symbol,
                message=f"{event}: {key.to_string()}",
            )
        )

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.strip().upper()
        if normalized.endswith(".TW") or normalized.endswith(".TWO"):
            return normalized
        if normalized.isdigit():
            return f"{normalized}.TW"
        return normalized
