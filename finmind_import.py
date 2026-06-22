from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import os
from pathlib import Path

from historical.repository import DEFAULT_DB_PATH, HistoricalSnapshotRepository
from historical.validation import HistoricalValidator
from importers.finmind import FinMindClient, FinMindConfig
from importers.finmind_importer import FinMindImporter
from importers.import_result import ImportResult


DEFAULT_SUMMARY_PATH = Path("reports/finmind_import_summary.md")
FINMIND_TOKEN_ENV = "FINMIND_TOKEN"


@dataclass
class FinMindImportSummary:
    symbol: str
    start_date: str | None
    end_date: str | None
    db_path: Path
    summary_path: Path
    imported_count: int = 0
    failed_count: int = 0
    warning_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def run_import(
    symbol: str,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
    token: str | None = None,
    summary_path: str | Path = DEFAULT_SUMMARY_PATH,
    importer: FinMindImporter | None = None,
) -> FinMindImportSummary:
    database_path = Path(db_path)
    output_path = Path(summary_path)
    repository = HistoricalSnapshotRepository(database_path)
    active_importer = importer or create_importer(token=token)

    import_result = active_importer.import_financial_statements(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        repository=repository,
    )

    summary = build_summary(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        db_path=database_path,
        summary_path=output_path,
        import_result=import_result,
    )
    write_summary(summary)
    return summary


def create_importer(token: str | None = None) -> FinMindImporter:
    config = FinMindConfig(token=token)
    client = FinMindClient(config=config)
    return FinMindImporter(client=client, validator=HistoricalValidator())


def build_summary(
    symbol: str,
    start_date: str | None,
    end_date: str | None,
    db_path: Path,
    summary_path: Path,
    import_result: ImportResult,
) -> FinMindImportSummary:
    return FinMindImportSummary(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        db_path=db_path,
        summary_path=summary_path,
        imported_count=import_result.imported_count,
        failed_count=import_result.failed_count,
        warning_count=len(import_result.warnings),
        errors=list(import_result.errors),
        warnings=list(import_result.warnings),
    )


def write_summary(summary: FinMindImportSummary) -> None:
    summary.summary_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# FinMind Import Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Symbol | {summary.symbol} |",
        f"| Start Date | {summary.start_date or ''} |",
        f"| End Date | {summary.end_date or ''} |",
        f"| Repository Database | {summary.db_path} |",
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


def resolve_token(cli_token: str | None, environ: dict[str, str] | None = None) -> str | None:
    env = environ if environ is not None else os.environ
    return (cli_token if cli_token is not None else env.get(FINMIND_TOKEN_ENV)) or None


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import FinMind financial statements into HistoricalSnapshotRepository"
    )
    parser.add_argument("--symbol", required=True, help="stock symbol, for example 2330 or 2330.TW")
    parser.add_argument("--start", dest="start_date", default=None, help="start date, YYYY-MM-DD")
    parser.add_argument("--end", dest="end_date", default=None, help="end date, YYYY-MM-DD")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite repository database path")
    parser.add_argument("--token", default=None, help="FinMind API token; falls back to FINMIND_TOKEN")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    token = resolve_token(args.token)

    summary = run_import(
        symbol=args.symbol,
        start_date=args.start_date,
        end_date=args.end_date,
        db_path=args.db,
        token=token,
        summary_path=DEFAULT_SUMMARY_PATH,
    )

    print("====================================")
    print(" StockAnalyzerPro FinMind Import")
    print("====================================")
    print(f"symbol={summary.symbol}")
    print(f"start_date={summary.start_date or ''}")
    print(f"end_date={summary.end_date or ''}")
    print(f"imported_count={summary.imported_count}")
    print(f"failed_count={summary.failed_count}")
    print(f"warning_count={summary.warning_count}")
    print(f"errors={len(summary.errors)}")
    print(f"warnings={len(summary.warnings)}")
    print(f"repository={summary.db_path}")
    print(f"summary={summary.summary_path}")
    return 0 if summary.failed_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
