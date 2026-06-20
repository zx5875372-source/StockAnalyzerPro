from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from models.financial_data import FinancialData


@dataclass(frozen=True)
class ProviderDiagnostic:
    provider: str
    severity: str
    message: str
    symbol: str | None = None


@dataclass(frozen=True)
class PriceHistory:
    symbol: str
    data: pd.DataFrame
    start: str | None = None
    end: str | None = None


class ProviderError(Exception):
    pass


class IDataProvider(ABC):
    name: str

    @abstractmethod
    def get_financial_data(self, symbol: str, as_of: str | None = None) -> FinancialData:
        raise NotImplementedError

    @abstractmethod
    def get_price_history(self, symbol: str, start: str, end: str) -> PriceHistory:
        raise NotImplementedError

    @abstractmethod
    def get_universe(self, universe_id: str) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def diagnostics(self) -> list[ProviderDiagnostic]:
        raise NotImplementedError
