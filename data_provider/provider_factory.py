from __future__ import annotations

from collections.abc import Callable

from data_provider.interfaces import IDataProvider, ProviderError


ProviderBuilder = Callable[..., IDataProvider]


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
        from data_provider.providers.csv_provider import CSVProvider
        from data_provider.providers.mock_provider import MockProvider
        from data_provider.providers.yahoo_finance_provider import YahooFinanceProvider

        factory = ProviderFactory()
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
