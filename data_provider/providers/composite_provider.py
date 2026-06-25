from __future__ import annotations

import json
from typing import Any

from data_provider.interfaces import IDataProvider, PriceHistory, ProviderDiagnostic, ProviderError
from data_provider.providers.finmind_provider import FinMindProvider
from data_provider.providers.yahoo_finance_provider import YahooFinanceProvider
from models.financial_data import FinancialData
from modules.downloader import normalize_symbol


class CompositeProvider(IDataProvider):
    name = "composite"
    version = "skeleton-v1"

    def __init__(
        self,
        primary_provider: IDataProvider | None = None,
        fallback_provider: IDataProvider | None = None,
    ):
        self.primary_provider = primary_provider or FinMindProvider()
        self.fallback_provider = fallback_provider or YahooFinanceProvider()
        self._diagnostics: list[ProviderDiagnostic] = []
        self._routing_diagnostics: list[dict[str, Any]] = []

    def get_financial_data(
        self,
        symbol: str,
        as_of: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinancialData:
        normalized_symbol = normalize_symbol(symbol)
        symbol_type = self.symbol_type(normalized_symbol)

        if symbol_type != "taiwan_stock":
            data = self._get_provider_financial_data(
                self.fallback_provider,
                normalized_symbol,
                as_of=as_of or end_date,
            )
            self._record_route(
                symbol=normalized_symbol,
                symbol_type=symbol_type,
                selected_provider=self._provider_name(self.fallback_provider),
                fallback_used=False,
                source_chain=[self._provider_name(self.fallback_provider)],
            )
            return data

        try:
            data = self._get_provider_financial_data(
                self.primary_provider,
                normalized_symbol,
                as_of=as_of,
                start_date=start_date,
                end_date=end_date,
            )
            self._record_route(
                symbol=normalized_symbol,
                symbol_type=symbol_type,
                selected_provider=self._provider_name(self.primary_provider),
                fallback_used=False,
                source_chain=[self._provider_name(self.primary_provider)],
            )
            return data
        except ProviderError as error:
            data = self._get_provider_financial_data(
                self.fallback_provider,
                normalized_symbol,
                as_of=as_of or end_date,
            )
            self._record_route(
                symbol=normalized_symbol,
                symbol_type=symbol_type,
                selected_provider=self._provider_name(self.fallback_provider),
                fallback_used=True,
                fallback_reason=str(error),
                source_chain=[
                    self._provider_name(self.primary_provider),
                    self._provider_name(self.fallback_provider),
                ],
            )
            return data

    def get_price_history(self, symbol: str, start: str, end: str) -> PriceHistory:
        normalized_symbol = normalize_symbol(symbol)
        result = self.fallback_provider.get_price_history(normalized_symbol, start=start, end=end)
        self._record_route(
            symbol=normalized_symbol,
            symbol_type=self.symbol_type(normalized_symbol),
            selected_provider=self._provider_name(self.fallback_provider),
            fallback_used=False,
            source_chain=[self._provider_name(self.fallback_provider)],
        )
        return result

    def get_universe(self, universe_id: str) -> list[str]:
        try:
            result = self.fallback_provider.get_universe(universe_id)
        except ProviderError:
            raise
        self._record_route(
            symbol=None,
            symbol_type="universe",
            selected_provider=self._provider_name(self.fallback_provider),
            fallback_used=False,
            source_chain=[self._provider_name(self.fallback_provider)],
        )
        return result

    def diagnostics(self) -> list[ProviderDiagnostic]:
        return list(self._diagnostics)

    def routing_diagnostics(self) -> list[dict[str, Any]]:
        return [dict(item) for item in self._routing_diagnostics]

    @staticmethod
    def symbol_type(symbol: str) -> str:
        normalized_symbol = normalize_symbol(symbol)
        if FinMindProvider.is_taiwan_symbol(normalized_symbol):
            return "taiwan_stock"
        return "non_taiwan"

    def _record_route(
        self,
        *,
        symbol: str | None,
        symbol_type: str,
        selected_provider: str,
        fallback_used: bool,
        source_chain: list[str],
        fallback_reason: str | None = None,
    ) -> None:
        route = {
            "primary_provider": self._provider_name(self.primary_provider),
            "fallback_provider": self._provider_name(self.fallback_provider),
            "selected_provider": selected_provider,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "symbol_type": symbol_type,
            "source_chain": source_chain,
        }
        self._routing_diagnostics.append(route)
        self._diagnostics.append(
            ProviderDiagnostic(
                provider=self.name,
                severity="info" if not fallback_used else "warning",
                symbol=symbol,
                message=json.dumps(route, ensure_ascii=False, sort_keys=True),
            )
        )

    @staticmethod
    def _provider_name(provider: IDataProvider) -> str:
        return getattr(provider, "name", provider.__class__.__name__).lower()

    @staticmethod
    def _get_provider_financial_data(
        provider: IDataProvider,
        symbol: str,
        as_of: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinancialData:
        if start_date is not None or end_date is not None:
            try:
                return provider.get_financial_data(
                    symbol,
                    as_of=as_of,
                    start_date=start_date,
                    end_date=end_date,
                )
            except TypeError:
                pass
        return provider.get_financial_data(symbol, as_of=as_of)
