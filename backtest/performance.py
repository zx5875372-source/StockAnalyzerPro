from models.financial_data import safe_divide


class PerformanceReport:
    def __init__(self, equity_curve: list[dict]):
        self.equity_curve = equity_curve

    def calculate(self) -> dict:
        if len(self.equity_curve) < 2:
            return {
                "total_return": 0,
                "cagr": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "sharpe": None,
                "sortino": None,
            }

        start_value = self.equity_curve[0]["total_value"]
        end_value = self.equity_curve[-1]["total_value"]
        total_return = safe_divide(end_value - start_value, start_value, precision=6) or 0
        cagr = self._cagr(start_value, end_value)
        max_drawdown = self._max_drawdown()
        win_rate = self._win_rate()

        return {
            "total_return": round(total_return, 4),
            "cagr": round(cagr, 4),
            "max_drawdown": round(max_drawdown, 4),
            "win_rate": round(win_rate, 4),
            "sharpe": None,
            "sortino": None,
        }

    def summary(self) -> dict:
        return self.calculate()

    def _cagr(self, start_value: float, end_value: float) -> float:
        if start_value <= 0 or end_value <= 0:
            return 0

        periods = len(self.equity_curve) - 1
        years = periods / 12
        if years <= 0:
            return 0

        return (end_value / start_value) ** (1 / years) - 1

    def _max_drawdown(self) -> float:
        peak = None
        max_drawdown = 0

        for row in self.equity_curve:
            value = row["total_value"]
            if peak is None or value > peak:
                peak = value
            drawdown = safe_divide(value - peak, peak, precision=6) or 0
            max_drawdown = min(max_drawdown, drawdown)

        return max_drawdown

    def _win_rate(self) -> float:
        returns = []
        previous_value = self.equity_curve[0]["total_value"]

        for row in self.equity_curve[1:]:
            value = row["total_value"]
            monthly_return = safe_divide(value - previous_value, previous_value, precision=6)
            if monthly_return is not None:
                returns.append(monthly_return)
            previous_value = value

        if not returns:
            return 0

        wins = sum(1 for value in returns if value > 0)
        return wins / len(returns)
