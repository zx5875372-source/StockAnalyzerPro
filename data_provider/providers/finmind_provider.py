from __future__ import annotations

from models.financial_data import FinancialData
from data_provider.interfaces import IDataProvider, PriceHistory, ProviderDiagnostic, ProviderError
from importers.finmind import FinMindClient
from modules.downloader import normalize_symbol


class FinMindProvider(IDataProvider):
    name = "finmind"
    version = "skeleton-v1"

    def __init__(self, client: object | None = None):
        self.client = client or FinMindClient()
        self._diagnostics: list[ProviderDiagnostic] = []

    def get_financial_data(self, symbol: str, as_of: str | None = None) -> FinancialData:
        normalized_symbol = self.normalize_symbol(symbol)
        if not self.is_taiwan_symbol(normalized_symbol):
            message = f"{normalized_symbol}: FinMindProvider supports Taiwan stock symbols only; use Yahoo fallback"
            self._record("warning", message, normalized_symbol)
            raise ProviderError(message)

        if hasattr(self.client, "get_financial_data"):
            try:
                return self.client.get_financial_data(normalized_symbol, as_of=as_of)
            except TypeError:
                return self.client.get_financial_data(normalized_symbol)

        message = (
            f"{normalized_symbol}: FinMindProvider FinancialData mapping is not implemented yet; "
            "use Yahoo fallback"
        )
        self._record("info", message, normalized_symbol)
        raise ProviderError(message)

    def get_price_history(self, symbol: str, start: str | None = None, end: str | None = None) -> PriceHistory:
        normalized_symbol = self.normalize_symbol(symbol)
        message = f"{normalized_symbol}: FinMindProvider price history is not implemented yet; use Yahoo fallback"
        self._record("info", message, normalized_symbol)
        raise ProviderError(message)

    def get_universe(self, universe_id: str) -> list[str]:
        message = f"{universe_id}: FinMindProvider universe lookup is not implemented yet"
        self._record("info", message)
        raise ProviderError(message)

    def diagnostics(self) -> list[ProviderDiagnostic]:
        return list(self._diagnostics)

    def get_provider_diagnostics(self) -> list[ProviderDiagnostic]:
        return self.diagnostics()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return normalize_symbol(symbol)

    @staticmethod
    def is_taiwan_symbol(symbol: str) -> bool:
        normalized = normalize_symbol(symbol)
        if normalized.endswith(".TW") or normalized.endswith(".TWO"):
            return normalized.split(".", 1)[0].isdigit()
        return False

    @staticmethod
    def finmind_stock_id(symbol: str) -> str:
        return normalize_symbol(symbol).split(".", 1)[0]

    def _record(self, severity: str, message: str, symbol: str | None = None) -> None:
        self._diagnostics.append(
            ProviderDiagnostic(
                provider=self.name,
                severity=severity,
                symbol=symbol,
                message=message,
            )
        )
