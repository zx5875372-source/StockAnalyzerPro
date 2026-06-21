import unittest

from strategy import BaseStrategy, StrategyContext, StrategyRegistry, StrategyRegistryError, StrategyResult
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
        strategy = registry.get("sap_score")

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


class DummyStrategy(BaseStrategy):
    name = "dummy"

    def evaluate(self, candidate, context=None):
        return StrategyResult(
            symbol=candidate["symbol"],
            strategy_name=self.name,
            score=candidate.get("score"),
            selected=True,
        )


if __name__ == "__main__":
    unittest.main()
