import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from strategy_compare import compare_strategies, write_reports


class StrategyCompareTests(unittest.TestCase):
    def test_compare_two_strategies_sorts_by_credibility_then_excess_return(self):
        args = make_args(["sap", "piotroski"])

        with patch("strategy_compare.BacktestEngine", FakeBacktestEngine):
            rows = compare_strategies(args)

        self.assertEqual([row["strategy"] for row in rows], ["Piotroski Strategy", "SAP Score Strategy MVP"])
        self.assertEqual(rows[0]["credibility_grade"], "B")
        self.assertEqual(rows[1]["credibility_grade"], "C")

    def test_unknown_strategy_name_raises_clear_error(self):
        args = make_args(["missing"])

        with self.assertRaisesRegex(ValueError, "Unknown strategy 'missing'"):
            compare_strategies(args)

    def test_write_reports_creates_csv_and_markdown(self):
        rows = [
            {
                "strategy": "Piotroski Strategy",
                "total_return": 0.2,
                "cagr": 0.1,
                "max_drawdown": -0.05,
                "win_rate": 0.6,
                "benchmark_total_return": 0.15,
                "excess_return": 0.05,
                "credibility_grade": "B",
                "selected_stock_count": 5,
                "skipped_stock_count": 2,
                "strategy_vs_benchmark": "outperform",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            md_path = Path(temp_dir) / "strategy_comparison.md"
            csv_path = Path(temp_dir) / "strategy_comparison.csv"

            write_reports(rows, md_path=md_path, csv_path=csv_path)

            markdown = md_path.read_text(encoding="utf-8")
            with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
                csv_rows = list(csv.DictReader(file))

        self.assertIn("# Strategy Comparison", markdown)
        self.assertIn("Piotroski Strategy", markdown)
        self.assertEqual(csv_rows[0]["strategy"], "Piotroski Strategy")
        self.assertEqual(csv_rows[0]["credibility_grade"], "B")


class FakeBacktestEngine:
    def __init__(self, strategy, portfolio, config):
        self.strategy = strategy
        self.portfolio = portfolio
        self.config = config

    def run(self):
        if self.config.strategy_name == "piotroski":
            return fake_result(
                strategy_name="Piotroski Strategy",
                credibility_grade="B",
                excess_return=0.03,
                selected_stock_count=5,
            )
        return fake_result(
            strategy_name="SAP Score Strategy MVP",
            credibility_grade="C",
            excess_return=0.5,
            selected_stock_count=1,
        )


def fake_result(strategy_name, credibility_grade, excess_return, selected_stock_count):
    return {
        "strategy_name": strategy_name,
        "metrics": {
            "total_return": 0.2,
            "cagr": 0.1,
            "max_drawdown": -0.05,
            "win_rate": 0.6,
            "benchmark_total_return": 0.15,
            "excess_return": excess_return,
            "strategy_vs_benchmark": "outperform" if excess_return > 0 else "underperform",
        },
        "credibility_grade": credibility_grade,
        "selected_stock_count": selected_stock_count,
        "skipped_stock_count": 2,
    }


def make_args(strategies):
    return argparse.Namespace(
        start="2023-01-01",
        end="2025-12-31",
        capital=1_000_000,
        benchmark="0050.TW",
        snapshot="data/snapshots/generated_sap_scores.csv",
        universe="tests/sample_data/sample_stocks.json",
        strategies=strategies,
    )


if __name__ == "__main__":
    unittest.main()
