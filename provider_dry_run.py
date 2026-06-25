from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from data_provider import PriceHistory, ProviderError, create_provider
from data_provider.interfaces import IDataProvider, ProviderDiagnostic
from data_provider.providers.composite_provider import CompositeProvider
from models.financial_data import FinancialData, FinancialPeriod
from modules.downloader import normalize_symbol


SUPPORTED_PROVIDERS = ("composite", "finmind", "yahoo")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Provider dry run diagnostics. This tool does not change runtime defaults.",
    )
    parser.add_argument("--provider", choices=SUPPORTED_PROVIDERS, default="composite")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--show-diagnostics", action="store_true")
    return parser.parse_args(argv)


def run_dry_run(args: argparse.Namespace, provider: IDataProvider | None = None) -> dict[str, Any]:
    provider_name = args.provider
    symbol = args.symbol
    normalized_symbol = normalize_symbol(symbol)
    selected_provider = None
    fallback_used = False
    fallback_reason = None
    symbol_type = CompositeProvider.symbol_type(normalized_symbol)
    source_chain: list[str] = []
    diagnostics: list[str] = []
    missing_fields_count = 0
    start_date = getattr(args, "start", None)
    end_date = getattr(args, "end", None)

    active_provider = provider or build_provider(provider_name, mock=args.mock)
    try:
        data = _get_financial_data(
            active_provider,
            symbol,
            start_date=start_date,
            end_date=end_date,
        )
        missing_fields_count = len(data.missing_fields)
        diagnostics.extend(data.diagnostics)
        route = _last_route(active_provider)
        if route:
            selected_provider = route.get("selected_provider")
            fallback_used = bool(route.get("fallback_used"))
            fallback_reason = route.get("fallback_reason")
            symbol_type = str(route.get("symbol_type") or symbol_type)
            source_chain = list(route.get("source_chain") or [])
        else:
            selected_provider = _provider_name(active_provider)
            source_chain = [selected_provider]

        diagnostics.extend(_provider_diagnostic_messages(active_provider))
        return {
            "success": True,
            "symbol": symbol,
            "normalized_symbol": normalized_symbol,
            "provider": provider_name,
            "selected_provider": selected_provider,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "symbol_type": symbol_type,
            "source_chain": source_chain,
            "missing_fields_count": missing_fields_count,
            "diagnostics": diagnostics,
            "error": None,
        }
    except Exception as error:
        diagnostics.extend(_provider_diagnostic_messages(active_provider))
        route = _last_route(active_provider)
        if route:
            selected_provider = route.get("selected_provider")
            fallback_used = bool(route.get("fallback_used"))
            fallback_reason = route.get("fallback_reason")
            source_chain = list(route.get("source_chain") or [])
        return {
            "success": False,
            "symbol": symbol,
            "normalized_symbol": normalized_symbol,
            "provider": provider_name,
            "selected_provider": selected_provider,
            "fallback_used": fallback_used,
            "fallback_reason": fallback_reason,
            "symbol_type": symbol_type,
            "source_chain": source_chain,
            "missing_fields_count": missing_fields_count,
            "diagnostics": diagnostics,
            "error": str(error),
        }


def build_provider(provider_name: str, mock: bool = False) -> IDataProvider:
    if not mock:
        return create_provider(provider_name)

    if provider_name == "composite":
        return build_mock_composite_provider()
    if provider_name == "finmind":
        return DryRunMockProvider("finmind", financial_data_by_symbol=_mock_financial_data(["2330.TW", "2330"]))
    if provider_name == "yahoo":
        return DryRunMockProvider("yahoo", financial_data_by_symbol=_mock_financial_data(["2330.TW", "AAPL"]))
    raise ProviderError(f"Unsupported provider for dry run: {provider_name}")


def build_mock_composite_provider(finmind_failure: Exception | None = None) -> CompositeProvider:
    finmind = DryRunMockProvider(
        "finmind",
        financial_data_by_symbol=_mock_financial_data(["2330.TW", "2454.TW"]),
        failure_by_symbol={"2330.TW": finmind_failure} if finmind_failure else None,
    )
    yahoo = DryRunMockProvider("yahoo", financial_data_by_symbol=_mock_financial_data(["2330.TW", "2454.TW", "AAPL"]))
    return CompositeProvider(primary_provider=finmind, fallback_provider=yahoo)


def format_result(result: dict[str, Any], show_diagnostics: bool = False) -> str:
    lines = [
        "Provider Dry Run",
        f"status: {'success' if result['success'] else 'failed'}",
        f"symbol: {result['symbol']}",
        f"normalized_symbol: {result['normalized_symbol']}",
        f"provider: {result['provider']}",
        f"selected_provider: {result.get('selected_provider') or '-'}",
        f"fallback_used: {str(result.get('fallback_used')).lower()}",
        f"fallback_reason: {result.get('fallback_reason') or '-'}",
        f"symbol_type: {result.get('symbol_type') or '-'}",
        f"missing_fields_count: {result.get('missing_fields_count', 0)}",
        f"source_chain: {' -> '.join(result.get('source_chain') or []) or '-'}",
    ]
    if result.get("error"):
        lines.append(f"error: {result['error']}")
    if show_diagnostics:
        lines.append("diagnostics:")
        diagnostics = result.get("diagnostics") or []
        if diagnostics:
            lines.extend([f"- {item}" for item in diagnostics])
        else:
            lines.append("- none")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_dry_run(args)
    print(format_result(result, show_diagnostics=args.show_diagnostics))
    return 0


def _last_route(provider: IDataProvider) -> dict[str, Any] | None:
    routing = getattr(provider, "routing_diagnostics", None)
    if not callable(routing):
        return None
    routes = routing()
    return routes[-1] if routes else None


def _provider_diagnostic_messages(provider: IDataProvider) -> list[str]:
    try:
        diagnostics = provider.diagnostics()
    except Exception:
        return []
    return [diagnostic.message for diagnostic in diagnostics]


def _provider_name(provider: IDataProvider) -> str:
    return getattr(provider, "name", provider.__class__.__name__).lower()


def _get_financial_data(
    provider: IDataProvider,
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
) -> FinancialData:
    if start_date is not None or end_date is not None:
        try:
            return provider.get_financial_data(symbol, start_date=start_date, end_date=end_date)
        except TypeError:
            return provider.get_financial_data(symbol, as_of=end_date)
    return provider.get_financial_data(symbol)


def _mock_financial_data(symbols: list[str]) -> dict[str, FinancialData]:
    data = {}
    for symbol in symbols:
        normalized_symbol = normalize_symbol(symbol)
        data[normalized_symbol] = FinancialData(
            symbol=normalized_symbol,
            company_name=f"mock {normalized_symbol}",
            current=FinancialPeriod(
                period="2024-12-31",
                revenue=1000,
                net_income=100,
                total_assets=2000,
                total_equity=1200,
                total_debt=800,
                gross_profit=500,
                operating_cashflow=180,
                free_cashflow=120,
                shares_outstanding=100,
                eps=1,
                book_value_per_share=12,
            ),
            previous=FinancialPeriod(period="2023-12-31", revenue=900, net_income=90),
            diagnostics=["mock financial data"],
        )
    return data


@dataclass
class DryRunMockProvider(IDataProvider):
    name: str
    financial_data_by_symbol: dict[str, FinancialData] = field(default_factory=dict)
    failure_by_symbol: dict[str, Exception | None] | None = None

    def get_financial_data(
        self,
        symbol: str,
        as_of: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinancialData:
        normalized_symbol = normalize_symbol(symbol)
        failure = (self.failure_by_symbol or {}).get(normalized_symbol)
        if failure is not None:
            raise failure
        data = self.financial_data_by_symbol.get(normalized_symbol)
        if data is None:
            raise ProviderError(f"{self.name}: mock financial data not found for {normalized_symbol}")
        return data

    def get_price_history(self, symbol: str, start: str, end: str) -> PriceHistory:
        normalized_symbol = normalize_symbol(symbol)
        frame = pd.DataFrame({"Close": [100.0, 101.0]})
        return PriceHistory(symbol=normalized_symbol, data=frame, start=start, end=end)

    def get_universe(self, universe_id: str) -> list[str]:
        raise ProviderError(f"{self.name}: mock universe not found for {universe_id}")

    def diagnostics(self) -> list[ProviderDiagnostic]:
        return []


if __name__ == "__main__":
    raise SystemExit(main())
