import argparse
import csv
import json
import time
from pathlib import Path

from modules.analyzer import analyze_stock
from modules.downloader import get_stock_data


SAMPLE_STOCKS_PATH = Path("tests/sample_data/sample_stocks.json")
WATCHLIST_PATH = Path("data/watchlist.json")
OUTPUT_PATH = Path("reports/scan_results.csv")
SUMMARY_PATH = Path("reports/scan_summary.md")
TOP10_PATH = Path("reports/top10.md")
WATCHLIST_REPORT_PATH = Path("reports/watchlist_report.md")


def load_sample_stocks(path: Path = SAMPLE_STOCKS_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_watchlist(path: Path = WATCHLIST_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        items = json.load(file)

    stocks = []
    for item in items:
        if isinstance(item, str):
            stocks.append({"symbol": item, "name": "", "category": "watchlist"})
        else:
            stocks.append(
                {
                    "symbol": item["symbol"],
                    "name": item.get("name", ""),
                    "category": item.get("category", "watchlist"),
                }
            )
    return stocks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="StockAnalyzerPro batch scanner")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--sample", action="store_true", help="scan tests/sample_data/sample_stocks.json")
    source.add_argument("--watchlist", action="store_true", help="scan data/watchlist.json")
    return parser.parse_args()


def load_scan_source(args: argparse.Namespace) -> tuple[str, list[dict]]:
    if args.sample:
        return "sample", load_sample_stocks()
    return "watchlist", load_watchlist()


def data_quality_score(missing_count: int) -> int:
    return max(100 - missing_count * 5, 0)


def valuation_available_count(valuation: dict) -> int:
    return sum(
        1
        for key in ["pe_fair_price", "pb_fair_price"]
        if valuation.get(key) is not None
    )


def growth_available_count(growth: dict) -> int:
    return sum(1 for item in growth.get("items", []) if item.get("growth_rate") is not None)


def scan_missing_fields(result: dict) -> list[str]:
    missing_fields = list(result.get("missing_fields", []))
    diagnostics = result.get("diagnostics", [])

    if any("缺少最新年度財報資料" in item for item in diagnostics):
        missing_fields.append("current.financial_period")
    if any("缺少前一年度財報資料" in item for item in diagnostics):
        missing_fields.append("previous.financial_period")

    return missing_fields


def below_reasonable_buy(price, reasonable_buy) -> str:
    if price is None or reasonable_buy is None:
        return "資料不足"
    return "是" if price <= reasonable_buy else "否"


def sort_rows(rows: list[dict]) -> list[dict]:
    def sort_key(row: dict):
        sap_score = row["sap_score"] if isinstance(row["sap_score"], (int, float)) else -1
        quality_score = row["data_quality_score"] if isinstance(row["data_quality_score"], int) else -1
        return sap_score, quality_score

    return sorted(rows, key=sort_key, reverse=True)


def scan_stock(stock: dict) -> dict:
    symbol = stock["symbol"]
    started_at = time.perf_counter()

    try:
        data = get_stock_data(symbol)
        result = analyze_stock(data)
        elapsed_seconds = round(time.perf_counter() - started_at, 2)
        piotroski = result["piotroski"]
        valuation = result["valuation"]
        growth = result["growth"]
        missing_fields = scan_missing_fields(result)
        missing_count = len(missing_fields)

        return {
            "symbol": result["symbol"],
            "name": stock.get("name", ""),
            "category": stock.get("category", ""),
            "status": "success",
            "sap_score": result["sap_score"],
            "grade": result["grade"],
            "price": result.get("price"),
            "piotroski_score": piotroski["score"],
            "piotroski_available": piotroski["available"],
            "piotroski_total": piotroski["total"],
            "valuation_available": valuation_available_count(valuation),
            "growth_available": growth_available_count(growth),
            "fair_price": valuation.get("fair_price"),
            "reasonable_buy": valuation.get("reasonable_buy"),
            "first_target_price": valuation.get("first_target_price"),
            "below_reasonable_buy": below_reasonable_buy(result.get("price"), valuation.get("reasonable_buy")),
            "missing_count": missing_count,
            "missing_fields": " | ".join(missing_fields),
            "data_quality_score": data_quality_score(missing_count),
            "diagnostics_count": len(result.get("diagnostics", [])),
            "diagnostics": " | ".join(result.get("diagnostics", [])),
            "elapsed_seconds": elapsed_seconds,
            "error": "",
        }
    except Exception as error:
        elapsed_seconds = round(time.perf_counter() - started_at, 2)
        return {
            "symbol": symbol,
            "name": stock.get("name", ""),
            "category": stock.get("category", ""),
            "status": "failed",
            "sap_score": "",
            "grade": "",
            "price": "",
            "piotroski_score": "",
            "piotroski_available": "",
            "piotroski_total": "",
            "valuation_available": "",
            "growth_available": "",
            "fair_price": "",
            "reasonable_buy": "",
            "first_target_price": "",
            "below_reasonable_buy": "",
            "missing_count": "",
            "missing_fields": "",
            "data_quality_score": "",
            "diagnostics_count": "",
            "diagnostics": "",
            "elapsed_seconds": elapsed_seconds,
            "error": str(error),
        }


def write_results(rows: list[dict], output_path: Path = OUTPUT_PATH) -> None:
    output_path.parent.mkdir(exist_ok=True)
    fieldnames = [
        "symbol",
        "name",
        "category",
        "status",
        "sap_score",
        "grade",
        "price",
        "piotroski_score",
        "piotroski_available",
        "piotroski_total",
        "valuation_available",
        "growth_available",
        "fair_price",
        "reasonable_buy",
        "first_target_price",
        "below_reasonable_buy",
        "missing_count",
        "missing_fields",
        "data_quality_score",
        "diagnostics_count",
        "diagnostics",
        "elapsed_seconds",
        "error",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def average(values: list[float]) -> float:
    if not values:
        return 0
    return round(sum(values) / len(values), 2)


def markdown_missing_fields(value: str) -> str:
    if not value:
        return "-"
    return value.replace(" | ", ", ")


def write_summary(rows: list[dict], output_path: Path = SUMMARY_PATH) -> None:
    output_path.parent.mkdir(exist_ok=True)

    success_rows = [row for row in rows if row["status"] == "success"]
    failed_rows = [row for row in rows if row["status"] != "success"]
    rows_by_missing = sorted(
        success_rows,
        key=lambda row: row["missing_count"] if isinstance(row["missing_count"], int) else -1,
        reverse=True,
    )
    top_score_rows = sorted(
        success_rows,
        key=lambda row: row["sap_score"] if isinstance(row["sap_score"], (int, float)) else -1,
        reverse=True,
    )

    avg_sap_score = average([row["sap_score"] for row in success_rows])
    avg_quality_score = average([row["data_quality_score"] for row in success_rows])

    missing_rows = "\n".join(
        [
            f"| {row['symbol']} | {row['name']} | {row['category']} | {row['missing_count']} | {row['data_quality_score']} | {markdown_missing_fields(row['missing_fields'])} |"
            for row in rows_by_missing[:10]
        ]
    )
    top_score_table_rows = "\n".join(
        [
            f"| {row['symbol']} | {row['name']} | {row['category']} | {row['sap_score']} | {row['grade']} | {row['data_quality_score']} |"
            for row in top_score_rows[:10]
        ]
    )

    content = f"""# Scan Summary

Version: v1.3 Ranking & Watchlist

| Metric | Value |
|---|---:|
| 總樣本數 | {len(rows)} |
| 成功數 | {len(success_rows)} |
| 失敗數 | {len(failed_rows)} |
| 平均 SAP Score | {avg_sap_score} |
| 平均資料品質分數 | {avg_quality_score} |

## 缺資料最多的前 10 檔

| 股票代號 | 名稱 | 類別 | Missing Count | Data Quality Score | Missing Fields |
|---|---|---|---:|---:|---|
{missing_rows}

## SAP Score 前 10 檔

| 股票代號 | 名稱 | 類別 | SAP Score | 等級 | Data Quality Score |
|---|---|---|---:|---|---:|
{top_score_table_rows}
"""

    output_path.write_text(content, encoding="utf-8")


def write_top10(rows: list[dict], output_path: Path = TOP10_PATH) -> None:
    output_path.parent.mkdir(exist_ok=True)
    success_rows = [row for row in rows if row["status"] == "success"]
    top_rows = sorted(
        success_rows,
        key=lambda row: row["sap_score"] if isinstance(row["sap_score"], (int, float)) else -1,
        reverse=True,
    )[:10]

    table_rows = "\n".join(
        [
            f"| {row['symbol']} | {row['name'] or '-'} | {row['category']} | {row['sap_score']} | {row['grade']} | {row['data_quality_score']} | {row['piotroski_score']} / {row['piotroski_total']} | {row['reasonable_buy'] or '資料不足'} | {row['first_target_price'] or '資料不足'} |"
            for row in top_rows
        ]
    )

    content = f"""# Top 10 Ranking

Version: v1.3 Ranking & Watchlist

| 股票代號 | 名稱 | 類別 | SAP Score | 等級 | 資料品質 | Piotroski | 合理買點 | 第一目標價 |
|---|---|---|---:|---|---:|---:|---:|---:|
{table_rows}
"""

    output_path.write_text(content, encoding="utf-8")


def write_watchlist_report(rows: list[dict], output_path: Path = WATCHLIST_REPORT_PATH) -> None:
    output_path.parent.mkdir(exist_ok=True)
    success_rows = [row for row in rows if row["status"] == "success"]

    table_rows = "\n".join(
        [
            f"| {row['symbol']} | {row['sap_score']} | {row['grade']} | {row['below_reasonable_buy']} | {row['first_target_price'] or '資料不足'} | {row['data_quality_score']} |"
            for row in success_rows
        ]
    )

    content = f"""# Watchlist Report

Version: v1.3 Ranking & Watchlist

| 股票代號 | SAP Score | 等級 | 低於合理買點 | 第一目標價 | 資料品質 |
|---|---:|---|---|---:|---:|
{table_rows}
"""

    output_path.write_text(content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    source_name, stocks = load_scan_source(args)
    rows = []

    print("====================================")
    print(" StockAnalyzerPro Scan v1.3")
    print("====================================")
    print(f"來源：{source_name}")
    print(f"樣本數：{len(stocks)}")

    for index, stock in enumerate(stocks, start=1):
        print(f"[{index}/{len(stocks)}] 分析 {stock['symbol']} {stock.get('name', '')}")
        rows.append(scan_stock(stock))

    sorted_rows = sort_rows(rows)
    write_results(sorted_rows)
    write_summary(sorted_rows)
    write_top10(sorted_rows)
    write_watchlist_report(sorted_rows)

    success_count = sum(1 for row in sorted_rows if row["status"] == "success")
    failed_count = len(sorted_rows) - success_count
    print("------------------------------------")
    print(f"完成：成功 {success_count}，失敗 {failed_count}")
    print(f"CSV：{OUTPUT_PATH}")
    print(f"Summary：{SUMMARY_PATH}")
    print(f"Top 10：{TOP10_PATH}")
    print(f"Watchlist：{WATCHLIST_REPORT_PATH}")


if __name__ == "__main__":
    main()
