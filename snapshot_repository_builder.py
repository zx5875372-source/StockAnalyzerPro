import argparse
from pathlib import Path

from historical.generator import NOT_POINT_IN_TIME_WARNING, SnapshotGenerator
from historical.repository import DEFAULT_DB_PATH, HistoricalSnapshotRepository
from scan import SAMPLE_STOCKS_PATH, load_sample_stocks


DEFAULT_SUMMARY_PATH = Path("reports/snapshot_repository_summary.md")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build HistoricalSnapshotRepository SAP Score snapshots")
    parser.add_argument("--universe", default=str(SAMPLE_STOCKS_PATH), help="sample stock universe JSON path")
    parser.add_argument("--database", default=str(DEFAULT_DB_PATH), help="SQLite repository database path")
    parser.add_argument("--output", default=str(DEFAULT_SUMMARY_PATH), help="summary Markdown output path")
    parser.add_argument("--snapshot-date", default=None, help="snapshot date in YYYY-MM-DD format")
    return parser.parse_args()


def write_summary(result, db_path: Path, universe_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Snapshot Repository Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Snapshot Date | {result.snapshot_date} |",
        f"| Database | {db_path} |",
        f"| Universe | {universe_path} |",
        f"| Total Stocks | {result.total_count} |",
        f"| Inserted Snapshots | {result.inserted_count} |",
        f"| Skipped Existing | {result.skipped_existing_count} |",
        f"| Failed Analysis | {result.failed_count} |",
        f"| Source | current_analysis_proxy |",
        f"| Source Version | v0 |",
        f"| Point In Time | false |",
        f"| Warning | {NOT_POINT_IN_TIME_WARNING} |",
        "",
        "## Inserted Symbols",
        "",
    ]

    if result.snapshots:
        lines.extend(f"- {snapshot.symbol}" for snapshot in result.snapshots)
    else:
        lines.append("- None")

    lines.extend(["", "## Failures", ""])
    if result.failures:
        lines.extend(f"- {failure.symbol}: {failure.error}" for failure in result.failures)
    else:
        lines.append("- None")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    universe_path = Path(args.universe)
    db_path = Path(args.database)
    output_path = Path(args.output)

    stocks = load_sample_stocks(universe_path)
    repository = HistoricalSnapshotRepository(db_path)
    generator = SnapshotGenerator(repository)

    print("====================================")
    print(" StockAnalyzerPro Repository Builder")
    print("====================================")
    print(f"股票數：{len(stocks)}")
    print(f"資料庫：{db_path}")
    print(f"輸出：{output_path}")
    print("------------------------------------")

    result = generator.generate(stocks, snapshot_date=args.snapshot_date)
    write_summary(result, db_path, universe_path, output_path)

    print("------------------------------------")
    print(f"snapshot_date={result.snapshot_date}")
    print(f"inserted={result.inserted_count}")
    print(f"skipped_existing={result.skipped_existing_count}")
    print(f"failed={result.failed_count}")
    print(f"warning={NOT_POINT_IN_TIME_WARNING}")
    print(f"summary={output_path}")


if __name__ == "__main__":
    main()
