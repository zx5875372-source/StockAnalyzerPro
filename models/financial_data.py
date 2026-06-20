from dataclasses import dataclass


@dataclass
class FinancialData:
    symbol: str
    company_name: str | None = None
    industry: str | None = None
    sector: str | None = None
    price: float | None = None
    net_income: float | None = None
    total_assets: float | None = None
    total_equity: float | None = None
    total_debt: float | None = None
    current_assets: float | None = None
    current_liabilities: float | None = None
    revenue: float | None = None
    gross_profit: float | None = None
    operating_income: float | None = None
    operating_cashflow: float | None = None
    free_cashflow: float | None = None
    shares_outstanding: float | None = None
    pe: float | None = None
    pb: float | None = None

    def roe(self) -> float | None:
        return _ratio_percent(self.net_income, self.total_equity)

    def roa(self) -> float | None:
        return _ratio_percent(self.net_income, self.total_assets)

    def debt_to_equity(self) -> float | None:
        return _ratio_percent(self.total_debt, self.total_equity)

    def current_ratio(self) -> float | None:
        return _safe_ratio(self.current_assets, self.current_liabilities)


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator, 2)


def _ratio_percent(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator * 100, 2)
