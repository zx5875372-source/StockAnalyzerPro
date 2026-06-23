import argparse
import csv
from pathlib import Path

from backtest.cli import (
    DEFAULT_BENCHMARK,
    DEFAULT_CAPITAL,
    DEFAULT_END,
    DEFAULT_SNAPSHOT,
    DEFAULT_SNAPSHOT_DB,
    DEFAULT_START,
    DEFAULT_UNIVERSE,
    build_config_from_args,
)
from backtest.engine import BacktestEngine
from backtest.portfolio import Portfolio
from strategy.registry import StrategyRegistryError, create_default_registry


DEFAULT_STRATEGIES = ["sap", "piotroski"]
COMPARISON_MD_PATH = Path("reports/strategy_comparison.md")
COMPARISON_CSV_PATH = Path("reports/strategy_comparison.csv")
FIELDNAMES = [
    "strategy",
    "total_return",
    "cagr",
    "max_drawdown",
    "win_rate",
    "benchmark_total_return",
    "excess_return",
    "credibility_grade",
    "qualification_grade",
    "is_formal_point_in_time",
    "qualification_reason",
    "research_only_count",
    "selected_stock_count",
    "skipped_stock_count",
    "strategy_vs_benchmark",
]
CREDIBILITY_ORDER = {
    "A": 4,
    "B": 3,
    "C": 2,
    "D": 1,
}


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="比較 StockAnalyzerPro 策略績效")
    parser.add_argument("--start", default=DEFAULT_START, help="回測開始日期，格式 YYYY-MM-DD")
    parser.add_argument("--end", default=DEFAULT_END, help="回測結束日期，格式 YYYY-MM-DD")
    parser.add_argument("--capital", type=float, default=DEFAULT_CAPITAL, help="初始資金")
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK, help="基準指數代號")
    parser.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="snapshot CSV 路徑")
    parser.add_argument(
        "--snapshot-source",
        default="csv",
        choices=["csv", "repository"],
        help="snapshot 來源：csv 或 repository",
    )
    parser.add_argument("--snapshot-db", default=DEFAULT_SNAPSHOT_DB, help="historical snapshot SQLite 資料庫路徑")
    parser.add_argument("--universe", default=DEFAULT_UNIVERSE, help="股票範圍 JSON 路徑")
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=DEFAULT_STRATEGIES,
        help="要比較的策略名稱，例如：sap piotroski",
    )
    return parser


def parse_args(argv=None) -> argparse.Namespace:
    return create_parser().parse_args(argv)


def compare_strategies(args: argparse.Namespace) -> list[dict]:
    registry = create_default_registry()
    rows = []

    for strategy_name in args.strategies:
        strategy = create_strategy(registry, strategy_name)
        config_args = argparse.Namespace(**vars(args))
        config_args.strategy = strategy_name
        config = build_config_from_args(config_args)
        portfolio = Portfolio(initial_cash=config.initial_cash)
        engine = BacktestEngine(strategy=strategy, portfolio=portfolio, config=config)
        result = engine.run()
        rows.append(result_to_row(result))

    return sort_rows(rows)


def create_strategy(registry, strategy_name: str):
    try:
        return registry.get(
            strategy_name,
            min_sap_score=80,
            min_piotroski_score=7,
            min_data_quality_score=80,
        )
    except StrategyRegistryError as error:
        raise ValueError(str(error)) from error


def result_to_row(result: dict) -> dict:
    metrics = result["metrics"]
    return {
        "strategy": result["strategy_name"],
        "total_return": metrics["total_return"],
        "cagr": metrics["cagr"],
        "max_drawdown": metrics["max_drawdown"],
        "win_rate": metrics["win_rate"],
        "benchmark_total_return": metrics["benchmark_total_return"],
        "excess_return": metrics["excess_return"],
        "credibility_grade": result["credibility_grade"],
        "qualification_grade": result.get("qualification_grade", "N/A"),
        "is_formal_point_in_time": result.get("is_formal_point_in_time", False),
        "qualification_reason": result.get("qualification_reason", ""),
        "research_only_count": result.get("research_only_count", 0),
        "selected_stock_count": result["selected_stock_count"],
        "skipped_stock_count": result["skipped_stock_count"],
        "strategy_vs_benchmark": metrics["strategy_vs_benchmark"],
    }


def sort_rows(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: (
            CREDIBILITY_ORDER.get(row["credibility_grade"], 0),
            row["excess_return"] if row["excess_return"] is not None else float("-inf"),
        ),
        reverse=True,
    )


def write_reports(
    rows: list[dict],
    md_path: Path = COMPARISON_MD_PATH,
    csv_path: Path = COMPARISON_CSV_PATH,
) -> None:
    md_path.parent.mkdir(exist_ok=True)
    write_csv(rows, csv_path)
    write_markdown(rows, md_path)


def write_csv(rows: list[dict], output_path: Path) -> None:
    with output_path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict], output_path: Path) -> None:
    table_rows = "\n".join(
        [
            f"| {row['strategy']} | {format_percent(row['total_return'])} | {format_percent(row['cagr'])} | "
            f"{format_percent(row['max_drawdown'])} | {format_percent(row['win_rate'])} | "
            f"{format_percent(row['benchmark_total_return'])} | {format_percent(row['excess_return'])} | "
            f"{row['credibility_grade']} | {row['qualification_grade']} | "
            f"{format_bool(row['is_formal_point_in_time'])} | {format_research_only(row)} | "
            f"{row['selected_stock_count']} | {row['skipped_stock_count']} | "
            f"{format_strategy_vs_benchmark(row['strategy_vs_benchmark'])} |"
            for row in rows
        ]
    )
    content = f"""# 策略比較

| 策略 | 總報酬率 | 年化報酬率 | 最大回撤 | 勝率 | 基準總報酬率 | 超額報酬率 | 可信度 | 回測資格 | 正式 Point-in-Time | 僅供研究 | 入選 | 略過 | 是否勝過基準 |
|---|---:|---:|---:|---:|---:|---:|---|---|---|---|---:|---:|---|
{table_rows}
"""
    output_path.write_text(content, encoding="utf-8")


def format_percent(value) -> str:
    if value is None:
        return "基準資料不足"
    return f"{value * 100:.2f}%"


def format_bool(value) -> str:
    return "是" if parse_bool(value) else "否"


def format_research_only(row: dict) -> str:
    return "是" if int(row.get("research_only_count") or 0) > 0 else "否"


def format_strategy_vs_benchmark(value: str) -> str:
    if value == "outperform":
        return "是"
    if value == "underperform":
        return "否"
    return "基準資料不足"


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def main(argv=None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        rows = compare_strategies(args)
    except ValueError as error:
        parser.error(str(error))

    write_reports(rows)

    print("====================================")
    print(" StockAnalyzerPro 策略比較")
    print("====================================")
    print(f"策略：{', '.join(args.strategies)}")
    print(f"Markdown 報告：{COMPARISON_MD_PATH}")
    print(f"CSV 報告：{COMPARISON_CSV_PATH}")


if __name__ == "__main__":
    main()
