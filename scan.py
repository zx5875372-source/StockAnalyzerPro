import csv
import json
import time
from pathlib import Path

from modules.analyzer import analyze_stock
from modules.downloader import get_stock_data


SAMPLE_STOCKS_PATH = Path("tests/sample_data/sample_stocks.json")
OUTPUT_PATH = Path("reports/scan_results.csv")
SUMMARY_PATH = Path("reports/scan_summary.md")


def load_sample_stocks(path: Path = SAMPLE_STOCKS_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


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
        missing_fields = result.get("missing_fields", [])
        missing_count = len(missing_fields)

        return {
            "symbol": result["symbol"],
            "name": stock.get("name", ""),
            "category": stock.get("category", ""),
            "status": "success",
            "sap_score": result["sap_score"],
            "grade": result["grade"],
            "piotroski_score": piotroski["score"],
            "piotroski_available": piotroski["available"],
            "piotroski_total": piotroski["total"],
            "valuation_available": valuation_available_count(valuation),
            "growth_available": growth_available_count(growth),
            "fair_price": valuation.get("fair_price"),
            "first_target_price": valuation.get("first_target_price"),
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
            "piotroski_score": "",
            "piotroski_available": "",
            "piotroski_total": "",
            "valuation_available": "",
            "growth_available": "",
            "fair_price": "",
            "first_target_price": "",
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
        "piotroski_score",
        "piotroski_available",
        "piotroski_total",
        "valuation_available",
        "growth_available",
        "fair_price",
        "first_target_price",
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

Version: v1.2 Data Quality Improvement

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


def main() -> None:
    stocks = load_sample_stocks()
    rows = []

    print("====================================")
    print(" StockAnalyzerPro Scan v1.2")
    print("====================================")
    print(f"樣本數：{len(stocks)}")

    for index, stock in enumerate(stocks, start=1):
        print(f"[{index}/{len(stocks)}] 分析 {stock['symbol']} {stock.get('name', '')}")
        rows.append(scan_stock(stock))

    sorted_rows = sort_rows(rows)
    write_results(sorted_rows)
    write_summary(sorted_rows)

    success_count = sum(1 for row in sorted_rows if row["status"] == "success")
    failed_count = len(sorted_rows) - success_count
    print("------------------------------------")
    print(f"完成：成功 {success_count}，失敗 {failed_count}")
    print(f"CSV：{OUTPUT_PATH}")
    print(f"Summary：{SUMMARY_PATH}")


if __name__ == "__main__":
    main()
