from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from data_provider.interfaces import IDataProvider, PriceHistory, ProviderDiagnostic, ProviderError
from models.financial_data import FinancialData
from modules.downloader import normalize_symbol


class MockProvider(IDataProvider):
    name = "mock"

    def __init__(
        self,
        financial_data: Mapping[str, FinancialData] | None = None,
        price_history: Mapping[str, pd.DataFrame] | None = None,
        universes: Mapping[str, list[str]] | None = None,
        diagnostics: list[ProviderDiagnostic] | None = None,
        failures: Mapping[str, Exception] | None = None,
    ):
        self._financial_data = dict(financial_data or {})
        self._price_history = dict(price_history or {})
        self._universes = dict(universes or {})
        self._diagnostics = list(diagnostics or [])
        self._failures = dict(failures or {})

    def get_financial_data(self, symbol: str, as_of: str | None = None) -> FinancialData:
        normalized_symbol = normalize_symbol(symbol)
        self._raise_if_failed(f"financial:{normalized_symbol}")
        self._raise_if_failed(normalized_symbol)

        data = self._financial_data.get(normalized_symbol)
        if data is None:
            raise ProviderError(f"Mock financial data not found for {normalized_symbol}")
        return data

    def get_price_history(self, symbol: str, start: str, end: str) -> PriceHistory:
        normalized_symbol = normalize_symbol(symbol)
        self._raise_if_failed(f"price:{normalized_symbol}")
        self._raise_if_failed(normalized_symbol)

        data = self._price_history.get(normalized_symbol)
        if data is None:
            raise ProviderError(f"Mock price history not found for {normalized_symbol}")
        return PriceHistory(symbol=normalized_symbol, data=data.copy(), start=start, end=end)

    def get_universe(self, universe_id: str) -> list[str]:
        self._raise_if_failed(f"universe:{universe_id}")

        universe = self._universes.get(universe_id)
        if universe is None:
            raise ProviderError(f"Mock universe not found for {universe_id}")
        return [normalize_symbol(symbol) for symbol in universe]

    def diagnostics(self) -> list[ProviderDiagnostic]:
        return list(self._diagnostics)

    def _raise_if_failed(self, key: str) -> None:
        failure = self._failures.get(key)
        if failure is not None:
            raise failure
