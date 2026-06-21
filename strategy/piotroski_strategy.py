from __future__ import annotations

from strategy.base_strategy import BaseStrategy, StrategyContext
from strategy.strategy_result import StrategyResult


class PiotroskiStrategy(BaseStrategy):
    name = "Piotroski Strategy"
    version = "1.0"

    def __init__(
        self,
        min_sap_score: int | None = None,
        min_piotroski_score: int = 7,
        min_data_quality_score: int = 80,
    ):
        self.min_piotroski_score = min_piotroski_score
        self.min_data_quality_score = min_data_quality_score
        self.skipped_reasons = {}

    def evaluate(self, candidate: dict, context: StrategyContext | None = None) -> StrategyResult:
        symbol = candidate.get("symbol", "")
        selected = self._passes(candidate)
        reasons = []
        warnings = []

        if selected:
            reasons.append("meets Piotroski and data quality thresholds")
        else:
            threshold_reason = self._threshold_reason(candidate)
            if threshold_reason:
                warnings.append(threshold_reason)

        return StrategyResult(
            symbol=symbol,
            strategy_name=self.name,
            score=self._number(candidate.get("piotroski_score")),
            selected=selected,
            reasons=reasons,
            warnings=warnings,
            metrics={
                "piotroski_score": candidate.get("piotroski_score"),
                "sap_score": candidate.get("sap_score"),
                "data_quality_score": candidate.get("data_quality_score"),
            },
        )

    def required_fields(self) -> list[str]:
        return ["symbol", "piotroski_score", "data_quality_score"]

    def select_stocks(self, date, universe: list[dict], data: dict) -> list[str]:
        self.skipped_reasons = {}
        snapshots = data.get("snapshots")
        selected = []

        for stock in universe:
            symbol = stock["symbol"]
            if snapshots is None:
                self.skipped_reasons[symbol] = "missing snapshot store"
                continue

            row = snapshots.latest_before(symbol, date)
            if row is None:
                self.skipped_reasons[symbol] = f"no snapshot on or before {date_to_text(date)}"
                continue

            if self._passes(row):
                selected.append(row)
            else:
                self.skipped_reasons[symbol] = self._threshold_reason(row)

        selected.sort(
            key=lambda row: (
                row.get("piotroski_score") or 0,
                row.get("sap_score") or 0,
                row.get("data_quality_score") or 0,
            ),
            reverse=True,
        )
        return [row["symbol"] for row in selected]

    def rebalance(self, date, portfolio, selected: list[str]) -> dict[str, float]:
        if not selected:
            return {}

        weight = 1 / len(selected)
        return {symbol: weight for symbol in selected}

    def _passes(self, row: dict) -> bool:
        return (
            self._number(row.get("piotroski_score")) >= self.min_piotroski_score
            and self._number(row.get("data_quality_score")) >= self.min_data_quality_score
        )

    def _threshold_reason(self, row: dict) -> str:
        reasons = []
        if self._number(row.get("piotroski_score")) < self.min_piotroski_score:
            reasons.append(f"piotroski_score {row.get('piotroski_score')} < {self.min_piotroski_score}")
        if self._number(row.get("data_quality_score")) < self.min_data_quality_score:
            reasons.append(f"data_quality_score {row.get('data_quality_score')} < {self.min_data_quality_score}")
        return "; ".join(reasons)

    @staticmethod
    def _number(value) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        return -1


def date_to_text(date) -> str:
    if hasattr(date, "date"):
        return str(date.date())
    return str(date)
