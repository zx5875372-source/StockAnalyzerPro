from __future__ import annotations

import csv
from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from importers.base_importer import BaseImporter, ImporterError
from importers.import_result import ImportResult
from modules.downloader import normalize_symbol


BASE_REQUIRED_COLUMNS = {
    "symbol",
    "fiscal_year",
    "fiscal_quarter",
    "statement_date",
    "published_date",
    "snapshot_date",
    "source",
    "source_version",
    "is_point_in_time",
    "created_at",
}
FINANCIAL_REQUIRED_COLUMNS = BASE_REQUIRED_COLUMNS | {"statement_type"}
SAP_REQUIRED_COLUMNS = BASE_REQUIRED_COLUMNS | {"credibility_grade"}


class CSVHistoricalImporter(BaseImporter):
    name = "csv_historical"
    version = "v0"

    def __init__(self, validator=None):
        self.validator = validator

    def supports(self, snapshot_type: str) -> bool:
        try:
            normalize_snapshot_type(snapshot_type)
        except ImporterError:
            return False
        return True

    def import_snapshot(
        self,
        source: str | Path,
        snapshot_type: str | None = None,
    ) -> ImportResult:
        csv_path = Path(source)
        if not csv_path.exists():
            raise ImporterError(f"Historical import CSV not found: {csv_path}")

        with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            fieldnames = set(reader.fieldnames or [])
            resolved_type = normalize_snapshot_type(snapshot_type) if snapshot_type else infer_snapshot_type(fieldnames)
            validate_required_columns(fieldnames, resolved_type)

            financial_snapshots = []
            sap_snapshots = []
            errors = []

            for row_number, row in enumerate(reader, start=2):
                try:
                    if resolved_type == "financial_statement":
                        financial_snapshots.append(financial_snapshot_from_row(row))
                    else:
                        sap_snapshots.append(sap_score_snapshot_from_row(row))
                except (KeyError, TypeError, ValueError) as error:
                    errors.append(f"row {row_number}: {error}")

        return ImportResult(
            importer=self.name,
            importer_version=self.version,
            source=str(csv_path),
            imported_count=len(financial_snapshots) + len(sap_snapshots),
            failed_count=len(errors),
            financial_statement_snapshots=financial_snapshots,
            sap_score_snapshots=sap_snapshots,
            errors=errors,
        )

    def import_financial_statements(self, source: str | Path) -> ImportResult:
        return self.import_snapshot(source=source, snapshot_type="financial_statement")


def infer_snapshot_type(fieldnames: set[str]) -> str:
    if "statement_type" in fieldnames:
        return "financial_statement"
    if {"sap_score", "piotroski_score", "data_quality_score"} & fieldnames:
        return "sap_score"
    raise ImporterError("Unable to infer historical snapshot type from CSV columns")


def normalize_snapshot_type(snapshot_type: str) -> str:
    normalized = snapshot_type.strip().lower().replace("-", "_")
    if normalized in {"financial", "financial_statement", "financial_statements", "financial_statement_snapshot"}:
        return "financial_statement"
    if normalized in {"sap", "sap_score", "sap_score_snapshot"}:
        return "sap_score"
    raise ImporterError(f"Unsupported historical snapshot type: {snapshot_type}")


def validate_required_columns(fieldnames: set[str], snapshot_type: str) -> None:
    required_columns = FINANCIAL_REQUIRED_COLUMNS if snapshot_type == "financial_statement" else SAP_REQUIRED_COLUMNS
    missing_columns = sorted(required_columns - fieldnames)
    if missing_columns:
        raise ImporterError(
            f"Historical {snapshot_type} CSV missing required columns: {', '.join(missing_columns)}"
        )


def financial_snapshot_from_row(row: dict[str, str]) -> FinancialStatementSnapshot:
    return FinancialStatementSnapshot(
        symbol=normalize_symbol(row["symbol"]),
        fiscal_year=int(row["fiscal_year"]),
        fiscal_quarter=int(row["fiscal_quarter"]),
        statement_date=row["statement_date"],
        published_date=row["published_date"],
        snapshot_date=row["snapshot_date"],
        source=row["source"],
        source_version=row["source_version"],
        is_point_in_time=parse_bool(row["is_point_in_time"]),
        created_at=row["created_at"],
        statement_type=row["statement_type"],
        payload_json=row.get("payload_json") or "{}",
        warning=row.get("warning") or "",
    )


def sap_score_snapshot_from_row(row: dict[str, str]) -> SAPScoreSnapshot:
    return SAPScoreSnapshot(
        symbol=normalize_symbol(row["symbol"]),
        fiscal_year=int(row["fiscal_year"]),
        fiscal_quarter=int(row["fiscal_quarter"]),
        statement_date=row["statement_date"],
        published_date=row["published_date"],
        snapshot_date=row["snapshot_date"],
        source=row["source"],
        source_version=row["source_version"],
        is_point_in_time=parse_bool(row["is_point_in_time"]),
        created_at=row["created_at"],
        sap_score=parse_optional_float(row.get("sap_score")),
        piotroski_score=parse_optional_float(row.get("piotroski_score")),
        data_quality_score=parse_optional_float(row.get("data_quality_score")),
        credibility_grade=row["credibility_grade"],
        warning=row.get("warning") or "",
    )


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y"}:
        return True
    if normalized in {"0", "false", "no", "n"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def parse_optional_float(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    return float(value)
