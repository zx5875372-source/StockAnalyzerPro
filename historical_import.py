from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
import sqlite3
import sys

from historical.repository import DEFAULT_DB_PATH, HistoricalSnapshotRepository
from historical.validation import HistoricalValidator
from importers.base_importer import ImporterError
from importers.csv_historical_importer import CSVHistoricalImporter


DEFAULT_SUMMARY_PATH = Path("reports/historical_import_summary.md")
SNAPSHOT_TYPE_MAP = {
    "sap": "sap_score",
    "financial": "financial_statement",
}


@dataclass
class HistoricalImportSummary:
    snapshot_type: str
    file_path: Path
    db_path: Path
    summary_path: Path
    imported_count: int = 0
    failed_count: int = 0
    warning_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run_import(
    snapshot_type: str,
    file_path: str | Path,
    db_path: str | Path = DEFAULT_DB_PATH,
    summary_path: str | Path = DEFAULT_SUMMARY_PATH,
) -> HistoricalImportSummary:
    resolved_type = resolve_snapshot_type(snapshot_type)
    csv_path = Path(file_path)
    database_path = Path(db_path)
    output_path = Path(summary_path)

    importer = CSVHistoricalImporter(validator=HistoricalValidator())
    import_result = importer.import_snapshot(csv_path, snapshot_type=resolved_type)
    repository = HistoricalSnapshotRepository(database_path)

    imported_count = 0
    write_errors = []

    if resolved_type == "sap_score":
        for snapshot in import_result.sap_score_snapshots:
            try:
                repository.insert_sap_snapshot(snapshot)
                imported_count += 1
            except sqlite3.IntegrityError as error:
                write_errors.append(f"{snapshot.symbol}: repository insert failed: {error}")
    else:
        for snapshot in import_result.financial_statement_snapshots:
            try:
                repository.insert_financial_snapshot(snapshot)
                imported_count += 1
            except sqlite3.IntegrityError as error:
                write_errors.append(f"{snapshot.symbol}: repository insert failed: {error}")

    summary = HistoricalImportSummary(
        snapshot_type=snapshot_type,
        file_path=csv_path,
        db_path=database_path,
        summary_path=output_path,
        imported_count=imported_count,
        failed_count=import_result.failed_count + len(write_errors),
        warning_count=len(import_result.warnings),
        errors=import_result.errors + write_errors,
        warnings=import_result.warnings,
    )
    write_summary(summary)
    return summary


def write_summary(summary: HistoricalImportSummary) -> None:
    summary.summary_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Historical Import Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Type | {summary.snapshot_type} |",
        f"| File | {summary.file_path} |",
        f"| Database | {summary.db_path} |",
        f"| Imported Count | {summary.imported_count} |",
        f"| Failed Count | {summary.failed_count} |",
        f"| Warning Count | {summary.warning_count} |",
        "",
        "## Errors",
        "",
    ]

    if summary.errors:
        lines.extend(f"- {error}" for error in summary.errors)
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    if summary.warnings:
        lines.extend(f"- {warning}" for warning in summary.warnings)
    else:
        lines.append("- None")

    summary.summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_snapshot_type(snapshot_type: str) -> str:
    normalized = snapshot_type.strip().lower()
    if normalized not in SNAPSHOT_TYPE_MAP:
        available = ", ".join(sorted(SNAPSHOT_TYPE_MAP))
        raise ImporterError(f"Unsupported import type '{snapshot_type}'. Available types: {available}")
    return SNAPSHOT_TYPE_MAP[normalized]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import historical snapshot CSV into HistoricalSnapshotRepository")
    parser.add_argument("--type", choices=sorted(SNAPSHOT_TYPE_MAP), required=True, help="historical snapshot type")
    parser.add_argument("--file", required=True, help="historical CSV file path")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite repository database path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        summary = run_import(
            snapshot_type=args.type,
            file_path=args.file,
            db_path=args.db,
            summary_path=DEFAULT_SUMMARY_PATH,
        )
    except ImporterError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("====================================")
    print(" StockAnalyzerPro Historical Import")
    print("====================================")
    print(f"imported_count={summary.imported_count}")
    print(f"failed_count={summary.failed_count}")
    print(f"warning_count={summary.warning_count}")
    print(f"errors={len(summary.errors)}")
    print(f"warnings={len(summary.warnings)}")
    print(f"summary={summary.summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
