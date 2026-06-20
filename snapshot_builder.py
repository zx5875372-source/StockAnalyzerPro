import argparse
import csv
from pathlib import Path

from modules.downloader import normalize_symbol
from scan import load_sample_stocks, scan_stock


DEFAULT_DATES = [
    "2023-03-31",
    "2023-06-30",
    "2023-09-30",
    "2023-12-31",
    "2024-03-31",
    "2024-06-30",
    "2024-09-30",
    "2024-12-31",
    "2025-03-31",
    "2025-06-30",
    "2025-09-30",
    "2025-12-31",
]

DEFAULT_OUTPUT_PATH = Path("data/snapshots/generated_sap_scores.csv")
SNAPSHOT_FIELDNAMES = [
    "date",
    "symbol",
    "sap_score",
    "piotroski_score",
    "data_quality_score",
    "source",
    "warning",
]


def build_snapshot_rows(
    stocks: list[dict],
    dates: list[str] | None = None,
    scan_func=scan_stock,
    verbose: bool = True,
) -> list[dict]:
    snapshot_dates = dates or DEFAULT_DATES
    analysis_rows = []

    for index, stock in enumerate(stocks, start=1):
        if verbose:
            print(f"[{index}/{len(stocks)}] 建立 proxy snapshot {stock['symbol']} {stock.get('name', '')}")
        analysis_rows.append(to_snapshot_seed(stock, scan_func(stock)))

    rows = []
    for snapshot_date in snapshot_dates:
        for seed in analysis_rows:
            rows.append(
                {
                    "date": snapshot_date,
                    "symbol": seed["symbol"],
                    "sap_score": seed["sap_score"],
                    "piotroski_score": seed["piotroski_score"],
                    "data_quality_score": seed["data_quality_score"],
                    "source": "current_analysis_proxy",
                    "warning": seed["warning"],
                }
            )

    return rows


def to_snapshot_seed(stock: dict, analysis: dict) -> dict:
    symbol = analysis.get("symbol") or normalize_symbol(stock["symbol"])
    if analysis.get("status") != "success":
        return {
            "symbol": normalize_symbol(symbol),
            "sap_score": "",
            "piotroski_score": "",
            "data_quality_score": "",
            "warning": f"not_point_in_time; analysis_failed: {analysis.get('error', 'unknown error')}",
        }

    return {
        "symbol": normalize_symbol(symbol),
        "sap_score": analysis.get("sap_score", ""),
        "piotroski_score": analysis.get("piotroski_score", ""),
        "data_quality_score": analysis.get("data_quality_score", ""),
        "warning": "not_point_in_time",
    }


def write_snapshot(rows: list[dict], output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=SNAPSHOT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build SAP Score snapshot CSV")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="snapshot CSV output path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output)
    stocks = load_sample_stocks()

    print("====================================")
    print(" StockAnalyzerPro Snapshot Builder")
    print("====================================")
    print(f"股票數：{len(stocks)}")
    print(f"日期數：{len(DEFAULT_DATES)}")
    print(f"輸出：{output_path}")
    print("------------------------------------")

    rows = build_snapshot_rows(stocks, DEFAULT_DATES)
    write_snapshot(rows, output_path)

    print("------------------------------------")
    print(f"完成：{len(rows)} rows")
    print("source=current_analysis_proxy")
    print("warning=not_point_in_time")


if __name__ == "__main__":
    main()
