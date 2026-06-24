import argparse
import csv
import json
import time
from pathlib import Path

from modules.analyzer import analyze_stock
from modules.downloader import get_stock_data, normalize_symbol


SAMPLE_STOCKS_PATH = Path("tests/sample_data/sample_stocks.json")
WATCHLIST_PATH = Path("data/watchlist.json")
OUTPUT_PATH = Path("reports/scan_results.csv")
SUMMARY_PATH = Path("reports/scan_summary.md")
TOP10_PATH = Path("reports/top10.md")
WATCHLIST_REPORT_PATH = Path("reports/watchlist_report.md")
STOCK_NAME_FALLBACKS = {
    "2330.TW": "台積電",
    "2454.TW": "聯發科",
    "2327.TW": "國巨",
    "6271.TW": "同欣電",
    "3189.TW": "景碩",
    "3265.TWO": "台星科",
    "1605.TW": "華新",
    "6290.TWO": "良維",
    "2344.TW": "華邦電",
    "2408.TW": "南亞科",
    "6187.TW": "萬潤",
    "1735.TW": "日勝化",
    "9945.TW": "潤泰新",
}


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


def resolve_scan_mode(args: argparse.Namespace) -> str:
    if args.sample:
        return "sample"
    return "watchlist"


def load_scan_source(mode: str = "watchlist") -> tuple[str, list[dict]]:
    if mode == "sample":
        return "sample", load_sample_stocks()
    if mode == "watchlist":
        return "watchlist", load_watchlist()
    raise ValueError(f"不支援的掃描模式：{mode}")


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


def clean_stock_name(value) -> str:
    if value is None:
        return ""
    name = str(value).strip()
    if not name or name in {"-", "未知公司", "None", "nan"}:
        return ""
    return name


def resolve_stock_name(stock: dict, data) -> str:
    fallback_name = STOCK_NAME_FALLBACKS.get(normalize_symbol(stock["symbol"]))
    if fallback_name:
        return fallback_name

    company_name = clean_stock_name(getattr(data, "company_name", None))
    if company_name:
        return truncate_stock_name(company_name)

    return truncate_stock_name(clean_stock_name(stock.get("name"))) or "-"


def display_stock_name(row: dict) -> str:
    symbol = row.get("symbol")
    if symbol:
        fallback_name = STOCK_NAME_FALLBACKS.get(normalize_symbol(str(symbol)))
        if fallback_name:
            return fallback_name

    name = clean_stock_name(row.get("name"))
    if name:
        return truncate_stock_name(name)
    return "-"


def truncate_stock_name(name: str) -> str:
    if not name:
        return ""
    limit = 8 if contains_cjk(name) else 16
    if len(name) <= limit:
        return name
    return name[:limit] + "..."


def contains_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def sort_rows(rows: list[dict]) -> list[dict]:
    def sort_key(row: dict):
        sap_score = numeric_sort_value(row.get("sap_score"))
        quality_score = numeric_sort_value(row.get("data_quality_score"))
        return sap_score, quality_score

    return sorted(rows, key=sort_key, reverse=True)


def numeric_sort_value(value) -> float:
    if value in {None, ""}:
        return -1
    try:
        return float(value)
    except (TypeError, ValueError):
        return -1


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
            "name": resolve_stock_name(stock, data),
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
    numeric_values = []
    for value in values:
        if value in {None, ""}:
            continue
        try:
            numeric_values.append(float(value))
        except (TypeError, ValueError):
            continue
    if not numeric_values:
        return 0
    return round(sum(numeric_values) / len(numeric_values), 2)


def markdown_value(value) -> str:
    if value in {None, ""}:
        return "-"
    return str(value).replace("|", "/")


def format_decimal(value) -> str:
    if value in {None, ""}:
        return "-"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "-"


def format_integer(value) -> str:
    if value in {None, ""}:
        return "-"
    try:
        return str(int(round(float(value))))
    except (TypeError, ValueError):
        return "-"


def format_piotroski(row: dict) -> str:
    score = row.get("piotroski_score")
    total = row.get("piotroski_total")
    if score in {None, ""} or total in {None, ""}:
        return "-"
    try:
        return f"{int(score)}/{int(total)}"
    except (TypeError, ValueError):
        return "-"


def recommendation_for_grade(grade: str) -> str:
    normalized = str(grade or "").strip().upper().replace("級", "")
    if normalized in {"S", "A"}:
        return "優先研究"
    if normalized == "B":
        return "可觀察"
    if normalized == "C":
        return "保守觀察"
    if normalized == "D":
        return "暫不建議"
    return "-"


def ranking_table_header() -> str:
    return """| 排名 | 股票代號 | 股票名稱 | SAP評分 | 等級 | Piotroski | 合理買點 | 第一目標價 | 建議 |
| -: | ---- | ---- | ----: | -- | --------: | ---: | ----: | -- |"""


def ranking_table(rows: list[dict], limit: int | None = None) -> str:
    selected_rows = rows[:limit] if limit is not None else rows
    if not selected_rows:
        return "| - | - | - | - | - | - | - | - | - |"

    table_rows = []
    for rank, row in enumerate(selected_rows, start=1):
        table_rows.append(
            "| "
            + " | ".join(
                [
                    str(rank),
                    markdown_value(row.get("symbol")),
                    markdown_value(display_stock_name(row)),
                    format_integer(row.get("sap_score")),
                    markdown_value(row.get("grade")),
                    format_piotroski(row),
                    format_decimal(row.get("reasonable_buy")),
                    format_decimal(row.get("first_target_price")),
                    recommendation_for_grade(row.get("grade")),
                ]
            )
            + " |"
        )
    return "\n".join(table_rows)


def report_header(title: str) -> str:
    return f"""# {title}

StockAnalyzerPro v3.0
股票分析系統"""


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
        key=lambda row: numeric_sort_value(row.get("missing_count")),
        reverse=True,
    )
    top_score_rows = sort_rows(success_rows)

    avg_sap_score = average([row["sap_score"] for row in success_rows])
    avg_quality_score = average([row["data_quality_score"] for row in success_rows])

    missing_rows = "\n".join(
        [
            f"| {index} | {markdown_value(row['symbol'])} | {markdown_value(display_stock_name(row))} | {format_integer(row['missing_count'])} | {format_integer(row['data_quality_score'])} | {markdown_missing_fields(row['missing_fields'])} |"
            for index, row in enumerate(rows_by_missing[:10], start=1)
        ]
    )
    if not missing_rows:
        missing_rows = "| - | - | - | - | - | - |"

    content = f"""{report_header("掃描摘要")}

| 指標 | 數值 |
|---|---:|
| 總樣本數 | {len(rows)} |
| 成功數 | {len(success_rows)} |
| 失敗數 | {len(failed_rows)} |
| 平均 SAP Score | {avg_sap_score} |
| 平均資料品質分數 | {avg_quality_score} |

## 缺資料最多的前 10 檔

| 排名 | 股票代號 | 股票名稱 | 缺值數 | 資料品質 | 缺值欄位 |
| -: | ---- | ---- | ---: | ---: | ---- |
{missing_rows}

## SAP Score 前 10 檔

{ranking_table_header()}
{ranking_table(top_score_rows, limit=10)}
"""

    output_path.write_text(content, encoding="utf-8")


def write_top10(rows: list[dict], output_path: Path = TOP10_PATH) -> None:
    output_path.parent.mkdir(exist_ok=True)
    success_rows = [row for row in rows if row["status"] == "success"]
    top_rows = sort_rows(success_rows)[:10]

    content = f"""{report_header("Top 10 排行榜")}

{ranking_table_header()}
{ranking_table(top_rows)}
"""

    output_path.write_text(content, encoding="utf-8")


def write_watchlist_report(rows: list[dict], output_path: Path = WATCHLIST_REPORT_PATH) -> None:
    output_path.parent.mkdir(exist_ok=True)
    success_rows = [row for row in rows if row["status"] == "success"]
    sorted_rows = sort_rows(success_rows)

    content = f"""{report_header("自選股分析報告")}

{ranking_table_header()}
{ranking_table(sorted_rows)}
"""

    output_path.write_text(content, encoding="utf-8")


def run_scan(mode: str = "watchlist") -> list[dict]:
    source_name, stocks = load_scan_source(mode)
    rows = []

    print("====================================")
    print(" StockAnalyzerPro v3.0 掃描")
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

    return sorted_rows


def main() -> None:
    args = parse_args()
    run_scan(resolve_scan_mode(args))


if __name__ == "__main__":
    main()
