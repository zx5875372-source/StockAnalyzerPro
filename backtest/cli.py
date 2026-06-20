import argparse
from pathlib import Path

import pandas as pd

from backtest.engine import BacktestConfig


DEFAULT_START = "2023-01-01"
DEFAULT_END = "2025-12-31"
DEFAULT_CAPITAL = 1_000_000
DEFAULT_BENCHMARK = "0050.TW"
DEFAULT_SNAPSHOT = "data/snapshots/generated_sap_scores.csv"
DEFAULT_UNIVERSE = "tests/sample_data/sample_stocks.json"


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="StockAnalyzerPro Backtest MVP")
    parser.add_argument("--start", default=DEFAULT_START, help="backtest start date, YYYY-MM-DD")
    parser.add_argument("--end", default=DEFAULT_END, help="backtest end date, YYYY-MM-DD")
    parser.add_argument("--capital", type=float, default=DEFAULT_CAPITAL, help="initial capital")
    parser.add_argument("--benchmark", default=DEFAULT_BENCHMARK, help="benchmark symbol")
    parser.add_argument("--snapshot", default=DEFAULT_SNAPSHOT, help="snapshot CSV path")
    parser.add_argument("--universe", default=DEFAULT_UNIVERSE, help="universe JSON path")
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

    snapshot_path = Path(args.snapshot)
    if not snapshot_path.exists():
        raise ValueError(f"snapshot 檔不存在：{snapshot_path}")

    universe_path = Path(args.universe)
    if not universe_path.exists():
        raise ValueError(f"universe 檔不存在：{universe_path}")

    return BacktestConfig(
        initial_cash=args.capital,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
        benchmark_symbol=args.benchmark,
        snapshot_path=snapshot_path,
        universe_path=universe_path,
    )
