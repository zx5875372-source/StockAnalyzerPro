from __future__ import annotations

from collections.abc import Callable

from strategy.base_strategy import BaseStrategy


StrategyBuilder = Callable[..., BaseStrategy]


class StrategyRegistryError(ValueError):
    pass


class StrategyRegistry:
    def __init__(self):
        self._builders: dict[str, StrategyBuilder] = {}

    def register(self, name: str, builder: StrategyBuilder) -> None:
        normalized_name = self._normalize_name(name)
        if normalized_name in self._builders:
            raise StrategyRegistryError(f"Strategy already registered: {name}")
        self._builders[normalized_name] = builder

    def unregister(self, name: str) -> None:
        normalized_name = self._normalize_name(name)
        if normalized_name not in self._builders:
            raise StrategyRegistryError(f"Strategy not registered: {name}")
        self._builders.pop(normalized_name)

    def get(self, name: str, **kwargs) -> BaseStrategy:
        normalized_name = self._normalize_name(name)
        builder = self._builders.get(normalized_name)
        if builder is None:
            available = ", ".join(self.list())
            raise StrategyRegistryError(f"Unknown strategy '{name}'. Available strategies: {available}")
        return builder(**kwargs)

    def list(self) -> list[str]:
        return sorted(self._builders)

    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower().replace("-", "_")


def create_default_registry() -> StrategyRegistry:
    from strategy.piotroski_strategy import PiotroskiStrategy
    from strategy.sap_strategy import SAPScoreStrategy

    registry = StrategyRegistry()
    registry.register("sap", SAPScoreStrategy)
    registry.register("sap_score", SAPScoreStrategy)
    registry.register("piotroski", PiotroskiStrategy)
    return registry
