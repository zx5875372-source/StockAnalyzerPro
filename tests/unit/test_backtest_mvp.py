import unittest

import pandas as pd

from backtest.engine import BacktestConfig, BacktestEngine
from backtest.performance import PerformanceReport
from backtest.portfolio import Portfolio
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
            "score_rows": {
                "2330.TW": {
                    "symbol": "2330.TW",
                    "sap_score": 90,
                    "piotroski_score": 8,
                    "data_quality_score": 100,
                },
                "2454.TW": {
                    "symbol": "2454.TW",
                    "sap_score": 79,
                    "piotroski_score": 8,
                    "data_quality_score": 100,
                },
                "0050.TW": {
                    "symbol": "0050.TW",
                    "sap_score": 95,
                    "piotroski_score": 2,
                    "data_quality_score": 100,
                },
            }
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
        engine.score_rows = {
            "2330.TW": {
                "symbol": "2330.TW",
                "sap_score": 90,
                "piotroski_score": 8,
                "data_quality_score": 100,
            }
        }
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


if __name__ == "__main__":
    unittest.main()
