from dataclasses import dataclass, field
import math


@dataclass
class FinancialPeriod:
    period: str | None = None
    net_income: float | None = None
    total_assets: float | None = None
    total_equity: float | None = None
    total_debt: float | None = None
    long_term_debt: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    revenue: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None
    operating_cashflow: float | None = None
    free_cashflow: float | None = None
    shares_outstanding: float | None = None


@dataclass
class FinancialData:
    symbol: str
    company_name: str | None = None
    industry: str | None = None
    sector: str | None = None
    price: float | None = None
    pe: float | None = None
    pb: float | None = None
    current: FinancialPeriod = field(default_factory=FinancialPeriod)
    previous: FinancialPeriod | None = None
    missing_fields: list[str] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)

    def roe(self) -> float | None:
        return ratio_percent(self.current.net_income, self.current.total_equity)

    def roa(self) -> float | None:
        return ratio_percent(self.current.net_income, self.current.total_assets)

    def debt_to_equity(self) -> float | None:
        return ratio_percent(self.current.total_debt, self.current.total_equity)

    def current_ratio(self) -> float | None:
        return safe_divide(self.current.current_assets, self.current.current_liabilities)


def is_valid_number(value: float | None) -> bool:
    if value is None:
        return False
    try:
        return not math.isnan(float(value))
    except (TypeError, ValueError):
        return False


def safe_divide(
    numerator: float | None,
    denominator: float | None,
    *,
    precision: int = 2,
    reject_non_positive_denominator: bool = True,
) -> float | None:
    if not is_valid_number(numerator) or not is_valid_number(denominator):
        return None

    denominator_value = float(denominator)
    if denominator_value == 0:
        return None
    if reject_non_positive_denominator and denominator_value <= 0:
        return None

    return round(float(numerator) / denominator_value, precision)


def ratio_percent(numerator: float | None, denominator: float | None) -> float | None:
    ratio = safe_divide(numerator, denominator, precision=4)
    if ratio is None:
        return None
    return round(ratio * 100, 2)
