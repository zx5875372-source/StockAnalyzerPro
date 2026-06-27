from __future__ import annotations

import json
from typing import Any

from data_provider.interfaces import IDataProvider, PriceHistory, ProviderDiagnostic, ProviderError
from data_provider.providers.finmind_provider import FinMindProvider
from data_provider.providers.yahoo_finance_provider import YahooFinanceProvider
from models.financial_data import FinancialData, safe_divide
from modules.downloader import normalize_symbol
from modules.stock_names import taiwan_stock_name


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
            self._enrich_with_fallback_market_data(data, normalized_symbol, as_of=as_of or end_date)
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

    def _enrich_with_fallback_market_data(
        self,
        data: FinancialData,
        symbol: str,
        as_of: str | None = None,
    ) -> None:
        enriched_fields: set[str] = set()
        derived_fields: set[str] = set()
        if self._apply_taiwan_name_fallback(data, symbol):
            enriched_fields.add("company_name")
        try:
            yahoo_data = self._get_provider_financial_data(self.fallback_provider, symbol, as_of=as_of)
        except Exception as error:
            data.diagnostics.append(f"yahoo_enrichment_failed: {error}")
            data.diagnostics.append("yahoo_enriched_fields: " + self._format_fields(enriched_fields))
            data.diagnostics.append("still_missing_fields: " + self._format_missing_fields(data))
            return

        if self._is_missing_text(data.company_name) and not self._is_missing_text(yahoo_data.company_name):
            data.company_name = yahoo_data.company_name
            enriched_fields.add("company_name")
        if self._is_missing_text(data.industry) and not self._is_missing_text(yahoo_data.industry):
            data.industry = yahoo_data.industry
            enriched_fields.add("industry")
        if self._is_missing_text(data.sector) and not self._is_missing_text(yahoo_data.sector):
            data.sector = yahoo_data.sector
            enriched_fields.add("sector")
        for field_name in ["price", "pe", "pb"]:
            if getattr(data, field_name, None) is None and getattr(yahoo_data, field_name, None) is not None:
                setattr(data, field_name, getattr(yahoo_data, field_name))
                enriched_fields.add(field_name)

        if data.pe is None and data.price is not None and data.current.eps is not None:
            data.pe = safe_divide(data.price, data.current.eps, precision=2)
            if data.pe is not None:
                derived_fields.add("pe")
        if data.pb is None and data.price is not None and data.current.book_value_per_share is not None:
            data.pb = safe_divide(data.price, data.current.book_value_per_share, precision=2)
            if data.pb is not None:
                derived_fields.add("pb")

        data.diagnostics.extend(
            [
                "yahoo_enriched_fields: " + self._format_fields(enriched_fields),
                "derived_fields: " + self._format_fields(derived_fields),
                "still_missing_fields: " + self._format_missing_fields(data),
            ]
        )

    @staticmethod
    def _apply_taiwan_name_fallback(data: FinancialData, symbol: str) -> bool:
        if CompositeProvider._is_missing_text(data.company_name):
            fallback_name = taiwan_stock_name(symbol)
            if fallback_name:
                data.company_name = fallback_name
                data.diagnostics.append(f"company_name_fallback: {fallback_name}")
                return True
        return False

    @staticmethod
    def _is_missing_text(value) -> bool:
        return value in {None, "", "-", "未知公司", "未知產業", "未知類別"}

    @staticmethod
    def _format_fields(fields: set[str]) -> str:
        if not fields:
            return "-"
        return ", ".join(sorted(fields))

    @staticmethod
    def _format_missing_fields(data: FinancialData) -> str:
        if not data.missing_fields:
            return "-"
        return ", ".join(data.missing_fields)

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
