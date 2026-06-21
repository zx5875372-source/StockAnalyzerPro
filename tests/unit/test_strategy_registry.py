import unittest

import pandas as pd

from backtest.snapshot import SnapshotScoreStore

from strategy import BaseStrategy, StrategyContext, StrategyRegistry, StrategyRegistryError, StrategyResult
from strategy.piotroski_strategy import PiotroskiStrategy
from strategy.registry import create_default_registry
from strategy.sap_strategy import SAPScoreStrategy


class StrategyRegistryTests(unittest.TestCase):
    def test_register_and_get_strategy(self):
        registry = StrategyRegistry()
        registry.register("dummy", DummyStrategy)

        strategy = registry.get("dummy")

        self.assertIsInstance(strategy, DummyStrategy)

    def test_duplicate_register_raises_clear_error(self):
        registry = StrategyRegistry()
        registry.register("dummy", DummyStrategy)

        with self.assertRaisesRegex(StrategyRegistryError, "already registered"):
            registry.register("dummy", DummyStrategy)

    def test_get_unknown_strategy_raises_clear_error(self):
        registry = StrategyRegistry()
        registry.register("dummy", DummyStrategy)

        with self.assertRaisesRegex(StrategyRegistryError, "Unknown strategy 'missing'.*dummy"):
            registry.get("missing")

    def test_list_returns_registered_strategy_names(self):
        registry = StrategyRegistry()
        registry.register("z-strategy", DummyStrategy)
        registry.register("a-strategy", DummyStrategy)

        self.assertEqual(registry.list(), ["a_strategy", "z_strategy"])

    def test_unregister_removes_strategy(self):
        registry = StrategyRegistry()
        registry.register("dummy", DummyStrategy)

        registry.unregister("dummy")

        self.assertEqual(registry.list(), [])
        with self.assertRaisesRegex(StrategyRegistryError, "Unknown strategy"):
            registry.get("dummy")

    def test_default_registry_executes_sap_strategy(self):
        registry = create_default_registry()
        strategy = registry.get("sap")

        result = strategy.evaluate(
            {
                "symbol": "2330.TW",
                "sap_score": 90,
                "piotroski_score": 8,
                "data_quality_score": 100,
            },
            StrategyContext(mode="unit_test"),
        )

        self.assertIsInstance(strategy, SAPScoreStrategy)
        self.assertIsInstance(result, StrategyResult)
        self.assertEqual(result.symbol, "2330.TW")
        self.assertEqual(result.strategy_name, SAPScoreStrategy.name)
        self.assertEqual(result.score, 90)
        self.assertTrue(result.selected)
        self.assertEqual(result.metrics["sap_score"], 90)

    def test_default_registry_has_sap_and_piotroski(self):
        registry = create_default_registry()

        self.assertIn("sap", registry.list())
        self.assertIn("piotroski", registry.list())
        self.assertIsInstance(registry.get("piotroski"), PiotroskiStrategy)

    def test_piotroski_strategy_selects_and_sorts_qualified_stocks(self):
        strategy = PiotroskiStrategy()
        universe = [
            {"symbol": "2330.TW"},
            {"symbol": "2454.TW"},
            {"symbol": "2327.TW"},
            {"symbol": "1605.TW"},
        ]
        data = {
            "snapshots": SnapshotScoreStore(
                [
                    snapshot_row("2024-01-01", "2330.TW", sap_score=70, piotroski_score=8, data_quality_score=90),
                    snapshot_row("2024-01-01", "2454.TW", sap_score=95, piotroski_score=8, data_quality_score=90),
                    snapshot_row("2024-01-01", "2327.TW", sap_score=99, piotroski_score=6, data_quality_score=100),
                    snapshot_row("2024-01-01", "1605.TW", sap_score=80, piotroski_score=7, data_quality_score=60),
                ]
            )
        }

        selected = strategy.select_stocks(pd.Timestamp("2024-01-31"), universe, data)

        self.assertEqual(selected, ["2454.TW", "2330.TW"])
        self.assertEqual(strategy.skipped_reasons["2327.TW"], "piotroski_score 6 < 7")
        self.assertEqual(strategy.skipped_reasons["1605.TW"], "data_quality_score 60 < 80")


class DummyStrategy(BaseStrategy):
    name = "dummy"

    def evaluate(self, candidate, context=None):
        return StrategyResult(
            symbol=candidate["symbol"],
            strategy_name=self.name,
            score=candidate.get("score"),
            selected=True,
        )


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
