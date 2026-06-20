from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    name = "BaseStrategy"

    @abstractmethod
    def select_stocks(self, date, universe: list[dict], data: dict) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def rebalance(self, date, portfolio, selected: list[str]) -> dict[str, float]:
        raise NotImplementedError


class SAPScoreStrategy(BaseStrategy):
    name = "SAP Score Strategy MVP"

    def __init__(
        self,
        min_sap_score: int = 80,
        min_piotroski_score: int = 7,
        min_data_quality_score: int = 80,
    ):
        self.min_sap_score = min_sap_score
        self.min_piotroski_score = min_piotroski_score
        self.min_data_quality_score = min_data_quality_score

    def select_stocks(self, date, universe: list[dict], data: dict) -> list[str]:
        score_rows = data.get("score_rows", {})
        selected = []

        for stock in universe:
            symbol = stock["symbol"]
            row = score_rows.get(symbol)
            if not row:
                continue

            if self._passes(row):
                selected.append(row)

        selected.sort(
            key=lambda row: (
                row.get("sap_score") or 0,
                row.get("piotroski_score") or 0,
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
            self._number(row.get("sap_score")) >= self.min_sap_score
            and self._number(row.get("piotroski_score")) >= self.min_piotroski_score
            and self._number(row.get("data_quality_score")) >= self.min_data_quality_score
        )

    @staticmethod
    def _number(value) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        return -1
