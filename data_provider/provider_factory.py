from __future__ import annotations

from collections.abc import Callable

from data_provider.interfaces import IDataProvider, ProviderError


ProviderBuilder = Callable[..., IDataProvider]
_SHARED_MEMORY_CACHES = {}


class ProviderFactory:
    def __init__(self):
        self._builders: dict[str, ProviderBuilder] = {}

    def register(self, name: str, builder: ProviderBuilder) -> None:
        normalized_name = self._normalize_name(name)
        self._builders[normalized_name] = builder

    def create(self, name: str, **kwargs) -> IDataProvider:
        normalized_name = self._normalize_name(name)
        builder = self._builders.get(normalized_name)
        if builder is None:
            available = ", ".join(sorted(self._builders))
            raise ProviderError(f"Unknown provider '{name}'. Available providers: {available}")
        return builder(**kwargs)

    @staticmethod
    def with_defaults() -> "ProviderFactory":
        from data_provider.cached_provider import CachedDataProvider
        from data_provider.providers.csv_provider import CSVProvider
        from data_provider.providers.mock_provider import MockProvider
        from data_provider.providers.yahoo_finance_provider import YahooFinanceProvider

        def build_cached_yahoo(**kwargs) -> IDataProvider:
            cache = kwargs.pop("cache", None) or _shared_memory_cache("cached_yahoo")
            ttl_seconds_by_data_type = kwargs.pop("ttl_seconds_by_data_type", None)
            provider = kwargs.pop("provider", None) or YahooFinanceProvider(**kwargs)
            return CachedDataProvider(
                provider=provider,
                cache=cache,
                ttl_seconds_by_data_type=ttl_seconds_by_data_type,
            )

        factory = ProviderFactory()
        factory.register("cached_yahoo", build_cached_yahoo)
        factory.register("csv", CSVProvider)
        factory.register("mock", MockProvider)
        factory.register("yahoo", YahooFinanceProvider)
        factory.register("yfinance", YahooFinanceProvider)
        factory.register("yahoo_finance", YahooFinanceProvider)
        return factory

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower().replace("-", "_")


def create_provider(name: str, **kwargs) -> IDataProvider:
    return ProviderFactory.with_defaults().create(name, **kwargs)


def _shared_memory_cache(name: str):
    from data_provider.cache import MemoryCache

    cache = _SHARED_MEMORY_CACHES.get(name)
    if cache is None:
        cache = MemoryCache()
        _SHARED_MEMORY_CACHES[name] = cache
    return cache
