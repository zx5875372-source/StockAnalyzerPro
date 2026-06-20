import csv
import json
import time
from pathlib import Path

from modules.analyzer import analyze_stock
from modules.downloader import get_stock_data


SAMPLE_STOCKS_PATH = Path("tests/sample_data/sample_stocks.json")
OUTPUT_PATH = Path("reports/scan_results.csv")


def load_sample_stocks(path: Path = SAMPLE_STOCKS_PATH) -> list[dict]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def scan_stock(stock: dict) -> dict:
    symbol = stock["symbol"]
    started_at = time.perf_counter()

    try:
        data = get_stock_data(symbol)
        result = analyze_stock(data)
        elapsed_seconds = round(time.perf_counter() - started_at, 2)
        piotroski = result["piotroski"]
        valuation = result["valuation"]

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
            "fair_price": valuation.get("fair_price"),
            "first_target_price": valuation.get("first_target_price"),
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
            "fair_price": "",
            "first_target_price": "",
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
        "fair_price",
        "first_target_price",
        "diagnostics_count",
        "diagnostics",
        "elapsed_seconds",
        "error",
    ]

    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    stocks = load_sample_stocks()
    rows = []

    print("====================================")
    print(" StockAnalyzerPro Scan v1.1")
    print("====================================")
    print(f"樣本數：{len(stocks)}")

    for index, stock in enumerate(stocks, start=1):
        print(f"[{index}/{len(stocks)}] 分析 {stock['symbol']} {stock.get('name', '')}")
        rows.append(scan_stock(stock))

    write_results(rows)

    success_count = sum(1 for row in rows if row["status"] == "success")
    failed_count = len(rows) - success_count
    print("------------------------------------")
    print(f"完成：成功 {success_count}，失敗 {failed_count}")
    print(f"CSV：{OUTPUT_PATH}")


if __name__ == "__main__":
    main()
