import argparse
from pathlib import Path

import pandas as pd

from backtest.engine import BacktestConfig


DEFAULT_START = "2023-01-01"
DEFAULT_END = "2025-12-31"
DEFAULT_CAPITAL = 1_000_000
DEFAULT_BENCHMARK = "0050.TW"
DEFAULT_SNAPSHOT = "data/snapshots/generated_sap_scores.csv"
DEFAULT_SNAPSHOT_DB = "historical_snapshots.db"
DEFAULT_UNIVERSE = "tests/sample_data/sample_stocks.json"
DEFAULT_STRATEGY = "sap"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StockAnalyzerPro 策略回測")
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
        "--strategy",
        default=DEFAULT_STRATEGY,
        choices=["sap", "piotroski"],
        help="策略名稱：sap 或 piotroski",
    )
    return parser


def parse_args(argv=None) -> argparse.Namespace:
    return create_parser().parse_args(argv)


def build_config_from_args(args: argparse.Namespace) -> BacktestConfig:
    start_date = pd.to_datetime(args.start, errors="coerce")
    end_date = pd.to_datetime(args.end, errors="coerce")
    if pd.isna(start_date):
        raise ValueError("start 必須是有效日期，格式 YYYY-MM-DD。")
    if pd.isna(end_date):
        raise ValueError("end 必須是有效日期，格式 YYYY-MM-DD。")
    if start_date > end_date:
        raise ValueError("start 不可晚於 end。")
    if args.capital <= 0:
        raise ValueError("capital 必須大於 0。")

    snapshot_source = getattr(args, "snapshot_source", "csv")
    snapshot_path = Path(args.snapshot)
    snapshot_db_path = Path(getattr(args, "snapshot_db", DEFAULT_SNAPSHOT_DB))
    if snapshot_source == "csv" and not snapshot_path.exists():
        raise ValueError(f"snapshot 檔不存在：{snapshot_path}")
    if snapshot_source == "repository" and not snapshot_db_path.exists():
        raise ValueError(f"snapshot repository db 不存在：{snapshot_db_path}")

    universe_path = Path(args.universe)
    if not universe_path.exists():
        raise ValueError(f"universe 檔不存在：{universe_path}")

    return BacktestConfig(
        initial_cash=args.capital,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        benchmark_symbol=args.benchmark,
        snapshot_path=snapshot_path,
        snapshot_source=snapshot_source,
        snapshot_db_path=snapshot_db_path,
        universe_path=universe_path,
        strategy_name=args.strategy,
    )
