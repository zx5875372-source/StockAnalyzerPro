from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from strategy.strategy_result import StrategyResult


@dataclass
class StrategyContext:
    as_of_date: object | None = None
    universe_name: str | None = None
    mode: str | None = None
    parameters: dict = field(default_factory=dict)


class BaseStrategy(ABC):
    name = "BaseStrategy"
    version = "1.0"

    @abstractmethod
    def evaluate(self, candidate: dict, context: StrategyContext | None = None) -> StrategyResult:
        raise NotImplementedError

    def rank(self, candidates: list[dict], context: StrategyContext | None = None) -> list[StrategyResult]:
        results = [self.evaluate(candidate, context) for candidate in candidates]
        ranked = sorted(
            results,
            key=lambda result: (
                result.selected,
                result.score if result.score is not None else -1,
                result.metrics.get("data_quality_score", -1),
                result.symbol,
            ),
            reverse=True,
        )
        for index, result in enumerate(ranked, start=1):
            result.rank = index
        return ranked

    def required_fields(self) -> list[str]:
        return []

    def select_stocks(self, date, universe: list[dict], data: dict) -> list[str]:
        raise NotImplementedError

    def rebalance(self, date, portfolio, selected: list[str]) -> dict[str, float]:
        raise NotImplementedError
