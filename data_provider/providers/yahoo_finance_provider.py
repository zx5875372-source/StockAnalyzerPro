from __future__ import annotations

from collections.abc import Callable

import pandas as pd
import yfinance as yf

from data_provider.interfaces import IDataProvider, PriceHistory, ProviderDiagnostic, ProviderError
from models.financial_data import FinancialData, FinancialPeriod
from modules.downloader import (
    build_diagnostics,
    build_period,
    normalize_number,
    normalize_symbol,
    safe_info_get,
)


class YahooFinanceProvider(IDataProvider):
    name = "yahoo"

    def __init__(self, ticker_factory: Callable[[str], object] | None = None):
        self._ticker_factory = ticker_factory or yf.Ticker
        self._diagnostics: list[ProviderDiagnostic] = []

    def get_info(self, symbol: str) -> dict:
        return dict(getattr(self._ticker(symbol), "info", {}) or {})

    def get_financials(self, symbol: str) -> pd.DataFrame:
        return self._statement(symbol, "financials")

    def get_balance_sheet(self, symbol: str) -> pd.DataFrame:
        return self._statement(symbol, "balance_sheet")

    def get_cashflow(self, symbol: str) -> pd.DataFrame:
        return self._statement(symbol, "cashflow")

    def get_history(
        self,
        symbol: str,
        start: str | None = None,
        end: str | None = None,
        period: str | None = None,
    ) -> pd.DataFrame:
        ticker = self._ticker(symbol)
        kwargs = {}
        if start is not None:
            kwargs["start"] = start
        if end is not None:
            kwargs["end"] = end
        if period is not None:
            kwargs["period"] = period
        return ticker.history(**kwargs)

    def get_financial_data(self, symbol: str, as_of: str | None = None) -> FinancialData:
        yf_symbol = normalize_symbol(symbol)
        info = self.get_info(yf_symbol)
        statements = {
            "financials": self.get_financials(yf_symbol),
            "balance_sheet": self.get_balance_sheet(yf_symbol),
            "cashflow": self.get_cashflow(yf_symbol),
        }

        if not info:
            raise ProviderError(f"{yf_symbol}: no company info returned from yfinance")

        missing_fields = []
        current = build_period(0, statements, info, missing_fields) or FinancialPeriod()
        previous = build_period(1, statements, info, missing_fields)
        diagnostics = build_diagnostics(current, previous, missing_fields)
        self._record_diagnostics(yf_symbol, diagnostics)

        return FinancialData(
            symbol=yf_symbol,
            company_name=safe_info_get(info, "longName", "未知公司"),
            industry=safe_info_get(info, "industry", "未知產業"),
            sector=safe_info_get(info, "sector", "未知類別"),
            price=normalize_number(safe_info_get(info, "currentPrice")),
            pe=normalize_number(safe_info_get(info, "trailingPE")),
            pb=normalize_number(safe_info_get(info, "priceToBook")),
            current=current,
            previous=previous,
            missing_fields=missing_fields,
            diagnostics=diagnostics,
        )

    def get_price_history(self, symbol: str, start: str, end: str) -> PriceHistory:
        yf_symbol = normalize_symbol(symbol)
        data = self.get_history(yf_symbol, start=start, end=end)
        if data.empty:
            self._diagnostics.append(
                ProviderDiagnostic(
                    provider=self.name,
                    severity="warning",
                    symbol=yf_symbol,
                    message="No historical price data returned",
                )
            )
        return PriceHistory(symbol=yf_symbol, data=data, start=start, end=end)

    def get_universe(self, universe_id: str) -> list[str]:
        raise ProviderError("YahooFinanceProvider does not provide universes")

    def diagnostics(self) -> list[ProviderDiagnostic]:
        return list(self._diagnostics)

    def _ticker(self, symbol: str):
        return self._ticker_factory(normalize_symbol(symbol))

    def _statement(self, symbol: str, attribute: str) -> pd.DataFrame:
        statement = getattr(self._ticker(symbol), attribute, None)
        if statement is None:
            return pd.DataFrame()
        return statement

    def _record_diagnostics(self, symbol: str, diagnostics: list[str]) -> None:
        for message in diagnostics:
            self._diagnostics.append(
                ProviderDiagnostic(
                    provider=self.name,
                    severity="warning",
                    symbol=symbol,
                    message=message,
                )
            )
