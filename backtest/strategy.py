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
        self.skipped_reasons = {}

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

    def _threshold_reason(self, row: dict) -> str:
        reasons = []
        if self._number(row.get("sap_score")) < self.min_sap_score:
            reasons.append(f"sap_score {row.get('sap_score')} < {self.min_sap_score}")
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
