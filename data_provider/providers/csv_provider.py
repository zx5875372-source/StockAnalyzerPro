from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from data_provider.interfaces import IDataProvider, PriceHistory, ProviderDiagnostic, ProviderError
from models.financial_data import FinancialData
from modules.downloader import normalize_symbol


SNAPSHOT_REQUIRED_COLUMNS = {
    "date",
    "symbol",
    "sap_score",
    "piotroski_score",
    "data_quality_score",
    "source",
    "warning",
}


class CSVProvider(IDataProvider):
    name = "csv"

    def __init__(self, fixture_root: str | Path = "data"):
        self.fixture_root = Path(fixture_root)
        self._diagnostics: list[ProviderDiagnostic] = []

    def read_snapshot(self, path: str | Path | None = None) -> list[dict[str, str]]:
        snapshot_path = Path(path) if path is not None else self.fixture_root / "snapshots" / "generated_sap_scores.csv"
        if not snapshot_path.exists():
            raise ProviderError(f"Snapshot CSV not found: {snapshot_path}")

        with snapshot_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            fieldnames = set(reader.fieldnames or [])
            missing_columns = sorted(SNAPSHOT_REQUIRED_COLUMNS - fieldnames)
            if missing_columns:
                raise ProviderError(
                    f"Snapshot CSV missing required columns: {', '.join(missing_columns)}"
                )

            rows = []
            for row_number, row in enumerate(reader, start=2):
                symbol = (row.get("symbol") or "").strip()
                if not symbol:
                    self._diagnostics.append(
                        ProviderDiagnostic(
                            provider=self.name,
                            severity="warning",
                            message=f"Snapshot row {row_number} missing symbol",
                        )
                    )
                    continue

                row["symbol"] = normalize_symbol(symbol)
                rows.append(row)

        return rows

    def get_financial_data(self, symbol: str, as_of: str | None = None) -> FinancialData:
        raise ProviderError("CSVProvider financial data is not implemented in this sprint")

    def get_price_history(self, symbol: str, start: str, end: str) -> PriceHistory:
        raise ProviderError("CSVProvider price history is not implemented in this sprint")

    def get_universe(self, universe_id: str) -> list[str]:
        path = self.fixture_root / f"{universe_id}.csv"
        if not path.exists():
            raise ProviderError(f"Universe CSV not found: {path}")

        frame = pd.read_csv(path)
        if "symbol" not in frame.columns:
            raise ProviderError("Universe CSV missing required column: symbol")

        return [normalize_symbol(symbol) for symbol in frame["symbol"].dropna().astype(str)]

    def diagnostics(self) -> list[ProviderDiagnostic]:
        return list(self._diagnostics)
