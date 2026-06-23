from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path

from historical.models import FinancialStatementSnapshot
from historical.repository import DEFAULT_DB_PATH, HistoricalSnapshotRepository
from historical.sap_generator import (
    DEFAULT_SUMMARY_PATH,
    HistoricalSAPGenerationResult,
    HistoricalSAPGenerator,
)


@dataclass
class HistoricalSAPGenerateSummary:
    db_path: Path
    summary_path: Path
    generated: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    filters: dict[str, str | int | None] = field(default_factory=dict)
    incremental: bool = False
    affected_periods: list[str] = field(default_factory=list)


def run_generate(
    db_path: str | Path = DEFAULT_DB_PATH,
    symbol: str | None = None,
    year: int | None = None,
    quarter: int | None = None,
    incremental: bool = False,
    summary_path: str | Path = DEFAULT_SUMMARY_PATH,
) -> HistoricalSAPGenerateSummary:
    database_path = Path(db_path)
    output_path = Path(summary_path)
    repository = HistoricalSnapshotRepository(database_path)
    generator = HistoricalSAPGenerator(repository=repository, summary_path=output_path)
    snapshots = filter_financial_snapshots(
        repository.list_financial_snapshots(),
        symbol=symbol,
        year=year,
        quarter=quarter,
    )

    if incremental:
        result = generator.generate_incremental(
            snapshots,
            repository=repository,
            write_report=False,
        )
    elif symbol is None and year is None and quarter is None:
        result = generator.generate_all(repository=repository)
    else:
        result = generator.generate_snapshots(
            snapshots,
            repository=repository,
            write_report=False,
        )

    summary = build_summary(
        db_path=database_path,
        summary_path=output_path,
        result=result,
        symbol=symbol,
        year=year,
        quarter=quarter,
        incremental=incremental,
    )
    write_summary(summary)
    return summary


def filter_financial_snapshots(
    snapshots: list[FinancialStatementSnapshot],
    symbol: str | None = None,
    year: int | None = None,
    quarter: int | None = None,
) -> list[FinancialStatementSnapshot]:
    normalized_symbol = normalize_symbol_filter(symbol) if symbol else None
    filtered = []
    for snapshot in snapshots:
        if normalized_symbol and snapshot.symbol != normalized_symbol:
            continue
        if year is not None and snapshot.fiscal_year != year:
            continue
        if quarter is not None and snapshot.fiscal_quarter != quarter:
            continue
        filtered.append(snapshot)
    return filtered


def normalize_symbol_filter(symbol: str) -> str:
    value = symbol.strip().upper()
    if value.isdigit():
        return f"{value}.TW"
    return value


def build_summary(
    db_path: Path,
    summary_path: Path,
    result: HistoricalSAPGenerationResult,
    symbol: str | None,
    year: int | None,
    quarter: int | None,
    incremental: bool = False,
) -> HistoricalSAPGenerateSummary:
    return HistoricalSAPGenerateSummary(
        db_path=db_path,
        summary_path=summary_path,
        generated=result.generated,
        updated=result.updated,
        skipped=result.skipped,
        failed=result.failed,
        warnings=list(result.warnings),
        errors=list(result.errors),
        filters={
            "symbol": normalize_symbol_filter(symbol) if symbol else None,
            "year": year,
            "quarter": quarter,
        },
        incremental=incremental,
        affected_periods=list(result.affected_periods),
    )


def write_summary(summary: HistoricalSAPGenerateSummary) -> None:
    summary.summary_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Historical Generator Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Database | {summary.db_path} |",
        f"| Incremental | {str(summary.incremental).lower()} |",
        f"| Generated | {summary.generated} |",
        f"| Updated | {summary.updated} |",
        f"| Skipped | {summary.skipped} |",
        f"| Failed | {summary.failed} |",
        f"| Warnings | {len(summary.warnings)} |",
        "",
        "## Filters Used",
        "",
        "| Filter | Value |",
        "| --- | --- |",
        f"| Symbol | {summary.filters.get('symbol') or 'ALL'} |",
        f"| Year | {summary.filters.get('year') or 'ALL'} |",
        f"| Quarter | {summary.filters.get('quarter') or 'ALL'} |",
        "",
        "## Affected Periods",
        "",
    ]
    if summary.affected_periods:
        lines.extend(f"- {period}" for period in summary.affected_periods)
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Warning Details",
        "",
    ])
    if summary.warnings:
        lines.extend(f"- {warning}" for warning in summary.warnings)
    else:
        lines.append("- None")

    lines.extend(["", "## Errors", ""])
    if summary.errors:
        lines.extend(f"- {error}" for error in summary.errors)
    else:
        lines.append("- None")

    summary.summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate historical SAP score snapshots from repository financial snapshots"
    )
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite historical snapshot database path")
    parser.add_argument("--symbol", default=None, help="optional stock symbol filter, for example 2330")
    parser.add_argument("--year", type=int, default=None, help="optional fiscal year filter")
    parser.add_argument("--quarter", type=int, choices=[1, 2, 3, 4], default=None, help="optional fiscal quarter")
    parser.add_argument("--incremental", action="store_true", help="generate only affected financial snapshot periods")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = run_generate(
        db_path=args.db,
        symbol=args.symbol,
        year=args.year,
        quarter=args.quarter,
        incremental=args.incremental,
        summary_path=DEFAULT_SUMMARY_PATH,
    )

    print("====================================")
    print(" StockAnalyzerPro Historical SAP Generator")
    print("====================================")
    print(f"db={summary.db_path}")
    print(f"generated={summary.generated}")
    print(f"updated={summary.updated}")
    print(f"skipped={summary.skipped}")
    print(f"failed={summary.failed}")
    print(f"warnings={len(summary.warnings)}")
    print(f"filters={summary.filters}")
    print(f"summary={summary.summary_path}")
    return 0 if summary.failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
