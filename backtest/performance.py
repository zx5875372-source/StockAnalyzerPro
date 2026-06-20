from models.financial_data import safe_divide


class PerformanceReport:
    def __init__(self, equity_curve: list[dict], benchmark_curve: list[dict] | None = None):
        self.equity_curve = equity_curve
        self.benchmark_curve = benchmark_curve or []

    def calculate(self) -> dict:
        if len(self.equity_curve) < 2:
            return {
                "total_return": 0,
                "cagr": 0,
                "max_drawdown": 0,
                "win_rate": 0,
                "sharpe": None,
                "sortino": None,
                "benchmark_total_return": None,
                "benchmark_cagr": None,
                "excess_return": None,
                "excess_cagr": None,
                "strategy_vs_benchmark": "benchmark unavailable",
            }

        start_value = self.equity_curve[0]["total_value"]
        end_value = self.equity_curve[-1]["total_value"]
        total_return = safe_divide(end_value - start_value, start_value, precision=6) or 0
        cagr = self._cagr(start_value, end_value)
        max_drawdown = self._max_drawdown()
        win_rate = self._win_rate()
        benchmark = self._benchmark_metrics(total_return, cagr)

        return {
            "total_return": round(total_return, 4),
            "cagr": round(cagr, 4),
            "max_drawdown": round(max_drawdown, 4),
            "win_rate": round(win_rate, 4),
            "sharpe": None,
            "sortino": None,
            **benchmark,
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

    def _benchmark_metrics(self, total_return: float, cagr: float) -> dict:
        if len(self.benchmark_curve) < 2:
            return {
                "benchmark_total_return": None,
                "benchmark_cagr": None,
                "excess_return": None,
                "excess_cagr": None,
                "strategy_vs_benchmark": "benchmark unavailable",
            }

        benchmark_start = self.benchmark_curve[0]["total_value"]
        benchmark_end = self.benchmark_curve[-1]["total_value"]
        benchmark_total_return = safe_divide(
            benchmark_end - benchmark_start,
            benchmark_start,
            precision=6,
        )
        if benchmark_total_return is None:
            return {
                "benchmark_total_return": None,
                "benchmark_cagr": None,
                "excess_return": None,
                "excess_cagr": None,
                "strategy_vs_benchmark": "benchmark unavailable",
            }

        benchmark_cagr = self._curve_cagr(self.benchmark_curve)
        excess_return = total_return - benchmark_total_return
        excess_cagr = cagr - benchmark_cagr

        return {
            "benchmark_total_return": round(benchmark_total_return, 4),
            "benchmark_cagr": round(benchmark_cagr, 4),
            "excess_return": round(excess_return, 4),
            "excess_cagr": round(excess_cagr, 4),
            "strategy_vs_benchmark": "outperform" if excess_return > 0 else "underperform",
        }

    def _curve_cagr(self, curve: list[dict]) -> float:
        if len(curve) < 2:
            return 0
        return self._cagr(curve[0]["total_value"], curve[-1]["total_value"])
