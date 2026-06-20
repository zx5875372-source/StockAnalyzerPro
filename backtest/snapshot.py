import csv
from pathlib import Path

import pandas as pd

from modules.downloader import normalize_symbol


REQUIRED_COLUMNS = {
    "date",
    "symbol",
    "sap_score",
    "piotroski_score",
    "data_quality_score",
}


class SnapshotScoreStore:
    def __init__(self, rows: list[dict] | None = None, source: Path | None = None, diagnostics: list[str] | None = None):
        self.rows = sorted(rows or [], key=lambda row: row["date"])
        self.source = source
        self.diagnostics = diagnostics or []

    @classmethod
    def from_csv(cls, path: Path):
        diagnostics = []
        if not path.exists():
            return cls(source=path, diagnostics=[f"snapshot missing: {path}"])

        rows = []
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
            if missing_columns:
                return cls(
                    source=path,
                    diagnostics=[f"snapshot missing columns: {', '.join(sorted(missing_columns))}"],
                )

            for line_number, row in enumerate(reader, start=2):
                normalized = normalize_snapshot_row(row)
                if normalized is None:
                    diagnostics.append(f"snapshot invalid row: line {line_number}")
                    continue
                rows.append(normalized)

        if not rows:
            diagnostics.append(f"snapshot empty: {path}")

        return cls(rows=rows, source=path, diagnostics=diagnostics)

    def latest_before(self, symbol: str, date) -> dict | None:
        normalized_symbol = normalize_symbol(symbol)
        target_date = pd.Timestamp(date)
        candidates = [
            row
            for row in self.rows
            if row["symbol"] == normalized_symbol and row["date"] <= target_date
        ]
        if not candidates:
            return None
        return candidates[-1]

    def available(self) -> bool:
        return bool(self.rows) and not any(item.startswith("snapshot missing") for item in self.diagnostics)

    def warning_counts(self) -> dict[str, int]:
        counts = {}
        for row in self.rows:
            warning = row.get("warning") or ""
            if not warning:
                continue
            counts[warning] = counts.get(warning, 0) + 1
        return counts

    def has_warnings(self) -> bool:
        return bool(self.warning_counts())


def normalize_snapshot_row(row: dict) -> dict | None:
    date = pd.to_datetime(row.get("date"), errors="coerce")
    if pd.isna(date):
        return None

    symbol = row.get("symbol")
    if not symbol:
        return None

    sap_score = parse_number(row.get("sap_score"))
    piotroski_score = parse_number(row.get("piotroski_score"))
    data_quality_score = parse_number(row.get("data_quality_score"))
    if sap_score is None or piotroski_score is None or data_quality_score is None:
        return None

    return {
        "date": pd.Timestamp(date),
        "symbol": normalize_symbol(symbol),
        "sap_score": sap_score,
        "piotroski_score": piotroski_score,
        "data_quality_score": data_quality_score,
        "source": row.get("source", ""),
        "warning": row.get("warning", ""),
    }


def parse_number(value):
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed.is_integer():
        return int(parsed)
    return parsed
