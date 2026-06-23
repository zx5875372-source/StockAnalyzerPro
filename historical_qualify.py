from __future__ import annotations

import argparse
from pathlib import Path

from historical.qualification import (
    DEFAULT_QUALIFICATION_REPORT_PATH,
    HistoricalQualifier,
    write_qualification_report,
)
from historical.repository import DEFAULT_DB_PATH, HistoricalSnapshotRepository


def run_qualification(
    db_path: str | Path = DEFAULT_DB_PATH,
    output_path: str | Path = DEFAULT_QUALIFICATION_REPORT_PATH,
):
    repository = HistoricalSnapshotRepository(db_path)
    result = HistoricalQualifier().qualify_repository(repository)
    write_qualification_report(result, output_path)
    return result


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Qualify historical snapshots for point-in-time research use")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite historical snapshot database path")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_QUALIFICATION_REPORT_PATH),
        help="qualification report path",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_qualification(args.db, args.output)

    print("====================================")
    print(" StockAnalyzerPro Historical Qualification")
    print("====================================")
    print(f"db={args.db}")
    print(f"total_snapshots={result.total_snapshots}")
    print(f"sap_snapshots={result.sap_snapshot_count}")
    print(f"qualified_sap_snapshots={result.qualified_sap_snapshot_count}")
    print(f"research_only_snapshots={result.research_only_count}")
    print(f"can_formal_backtest={str(result.can_formal_backtest).lower()}")
    print(f"summary={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
