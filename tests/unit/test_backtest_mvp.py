import unittest

import pandas as pd

from backtest.engine import BacktestConfig, BacktestEngine
from backtest.performance import PerformanceReport
from backtest.portfolio import Portfolio
from backtest.snapshot import SnapshotScoreStore
from backtest.strategy import SAPScoreStrategy


class BacktestMVPTests(unittest.TestCase):
    def test_sap_score_strategy_selects_only_qualified_stocks(self):
        strategy = SAPScoreStrategy()
        universe = [
            {"symbol": "2330.TW"},
            {"symbol": "2454.TW"},
            {"symbol": "0050.TW"},
        ]
        data = {
            "snapshots": SnapshotScoreStore(
                [
                    snapshot_row("2023-12-31", "2330.TW", 90, 8, 100),
                    snapshot_row("2023-12-31", "2454.TW", 79, 8, 100),
                    snapshot_row("2023-12-31", "0050.TW", 95, 2, 100),
                ]
            )
        }

        selected = strategy.select_stocks(pd.Timestamp("2024-01-31"), universe, data)

        self.assertEqual(selected, ["2330.TW"])

    def test_portfolio_rebalances_equal_weight_positions(self):
        portfolio = Portfolio(initial_cash=1_000_000)
        prices = {"2330.TW": 500, "2454.TW": 1000}

        portfolio.update_positions(
            pd.Timestamp("2024-01-31"),
            {"2330.TW": 0.5, "2454.TW": 0.5},
            prices,
        )

        self.assertAlmostEqual(portfolio.positions["2330.TW"], 1000)
        self.assertAlmostEqual(portfolio.positions["2454.TW"], 500)
        self.assertAlmostEqual(portfolio.total_value(prices), 1_000_000)

    def test_performance_report_calculates_basic_metrics(self):
        equity_curve = [
            {"date": "2024-01-01", "total_value": 1_000_000},
            {"date": "2024-01-31", "total_value": 1_100_000},
            {"date": "2024-02-29", "total_value": 1_050_000},
        ]

        metrics = PerformanceReport(equity_curve).calculate()

        self.assertEqual(metrics["total_return"], 0.05)
        self.assertLess(metrics["max_drawdown"], 0)
        self.assertEqual(metrics["win_rate"], 0.5)
        self.assertIsNone(metrics["sharpe"])
        self.assertIsNone(metrics["sortino"])

    def test_engine_runs_with_prefilled_data_without_network(self):
        config = BacktestConfig(
            initial_cash=1_000_000,
            start_date="2024-01-01",
            end_date="2024-03-31",
        )
        strategy = SAPScoreStrategy()
        portfolio = Portfolio(initial_cash=config.initial_cash)
        engine = BacktestEngine(strategy=strategy, portfolio=portfolio, config=config)
        engine.universe = [{"symbol": "2330.TW"}]
        engine.snapshots = SnapshotScoreStore(
            [snapshot_row("2023-12-31", "2330.TW", 90, 8, 100)]
        )
        engine.look_ahead_safe = True
        engine.price_history = {
            "2330.TW": pd.Series(
                [500, 550, 600],
                index=pd.to_datetime(["2024-01-31", "2024-02-29", "2024-03-29"]),
            )
        }

        result = engine.run()

        self.assertEqual(result["selected_symbols"], ["2330.TW"])
        self.assertGreater(result["metrics"]["total_return"], 0)
        self.assertGreaterEqual(len(result["equity_curve"]), 2)
        self.assertTrue(result["look_ahead_safe"])
        self.assertNotIn("2330.TW", result["skipped_reasons"])

    def test_snapshot_date_does_not_use_future_data(self):
        strategy = SAPScoreStrategy()
        universe = [{"symbol": "2330.TW"}]
        data = {
            "snapshots": SnapshotScoreStore(
                [
                    snapshot_row("2023-12-31", "2330.TW", 70, 8, 100),
                    snapshot_row("2024-12-31", "2330.TW", 90, 8, 100),
                ]
            )
        }

        selected = strategy.select_stocks(pd.Timestamp("2024-01-31"), universe, data)

        self.assertEqual(selected, [])
        self.assertIn("2330.TW", strategy.skipped_reasons)

    def test_stock_without_snapshot_is_skipped(self):
        strategy = SAPScoreStrategy()
        universe = [{"symbol": "2454.TW"}]
        data = {
            "snapshots": SnapshotScoreStore(
                [snapshot_row("2023-12-31", "2330.TW", 90, 8, 100)]
            )
        }

        selected = strategy.select_stocks(pd.Timestamp("2024-01-31"), universe, data)

        self.assertEqual(selected, [])
        self.assertEqual(
            strategy.skipped_reasons["2454.TW"],
            "no snapshot on or before 2024-01-31",
        )

    def test_strategy_does_not_fallback_to_current_score_rows(self):
        strategy = SAPScoreStrategy()
        universe = [{"symbol": "2330.TW"}]
        data = {
            "score_rows": {
                "2330.TW": {
                    "symbol": "2330.TW",
                    "sap_score": 99,
                    "piotroski_score": 9,
                    "data_quality_score": 100,
                }
            }
        }

        selected = strategy.select_stocks(pd.Timestamp("2024-01-31"), universe, data)

        self.assertEqual(selected, [])
        self.assertEqual(strategy.skipped_reasons["2330.TW"], "missing snapshot store")


def snapshot_row(date, symbol, sap_score, piotroski_score, data_quality_score):
    return {
        "date": pd.Timestamp(date),
        "symbol": symbol,
        "sap_score": sap_score,
        "piotroski_score": piotroski_score,
        "data_quality_score": data_quality_score,
    }


if __name__ == "__main__":
    unittest.main()
