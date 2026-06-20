from dataclasses import dataclass, field


@dataclass
class Portfolio:
    initial_cash: float = 1_000_000
    cash: float = field(init=False)
    positions: dict[str, float] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    equity_curve: list[dict] = field(default_factory=list)

    def __post_init__(self):
        self.cash = float(self.initial_cash)

    def total_value(self, prices: dict[str, float]) -> float:
        position_value = sum(
            shares * prices[symbol]
            for symbol, shares in self.positions.items()
            if symbol in prices and prices[symbol] is not None
        )
        return round(self.cash + position_value, 2)

    def update_positions(self, date, target_weights: dict[str, float], prices: dict[str, float]) -> None:
        portfolio_value = self.total_value(prices)
        new_positions = {}

        for symbol, weight in target_weights.items():
            price = prices.get(symbol)
            if price is None or price <= 0:
                self.record_history(date, f"skip {symbol}: missing price")
                continue

            target_value = portfolio_value * weight
            new_positions[symbol] = target_value / price

        invested_value = sum(
            shares * prices[symbol]
            for symbol, shares in new_positions.items()
            if symbol in prices
        )
        self.positions = new_positions
        self.cash = round(portfolio_value - invested_value, 2)
        self.record_history(date, f"rebalance {len(new_positions)} positions")

    def record_equity(self, date, prices: dict[str, float]) -> None:
        self.equity_curve.append(
            {
                "date": str(date.date() if hasattr(date, "date") else date),
                "total_value": self.total_value(prices),
                "cash": round(self.cash, 2),
                "positions": len(self.positions),
            }
        )

    def record_history(self, date, event: str) -> None:
        self.history.append(
            {
                "date": str(date.date() if hasattr(date, "date") else date),
                "event": event,
            }
        )
