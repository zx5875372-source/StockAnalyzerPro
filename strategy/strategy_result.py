from dataclasses import dataclass, field


@dataclass
class StrategyResult:
    symbol: str
    strategy_name: str
    score: float | None
    rank: int | None = None
    selected: bool = False
    reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
