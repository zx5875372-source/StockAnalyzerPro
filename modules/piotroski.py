from models.financial_data import FinancialData, FinancialPeriod, ratio_percent, safe_divide


def calculate_piotroski(data: FinancialData) -> dict:
    current = data.current
    previous = data.previous

    items = [
        evaluate_positive_roa(current),
        evaluate_positive_operating_cashflow(current),
        evaluate_roa_improvement(current, previous),
        evaluate_cashflow_greater_than_net_income(current),
        evaluate_long_term_debt_ratio_decline(current, previous),
        evaluate_current_ratio_improvement(current, previous),
        evaluate_no_share_dilution(current, previous),
        evaluate_gross_margin_improvement(current, previous),
        evaluate_asset_turnover_improvement(current, previous),
    ]

    score = sum(1 for item in items if item["passed"] is True)
    available = sum(1 for item in items if item["passed"] is not None)

    return {
        "score": score,
        "available": available,
        "total": 9,
        "items": items,
    }


def build_item(name: str, passed, current_value, previous_value, note: str) -> dict:
    return {
        "name": name,
        "passed": passed,
        "current_value": current_value,
        "previous_value": previous_value,
        "note": note,
    }


def pass_if_available(current_value, previous_value, comparison) -> bool | None:
    if current_value is None or previous_value is None:
        return None
    return comparison(current_value, previous_value)


def evaluate_positive_roa(current: FinancialPeriod) -> dict:
    current_roa = ratio_percent(current.net_income, current.total_assets)

    return build_item(
        "1. ROA 為正",
        None if current_roa is None else current_roa > 0,
        current_roa,
        None,
        "current ROA > 0 加 1 分",
    )


def evaluate_positive_operating_cashflow(current: FinancialPeriod) -> dict:
    operating_cashflow = current.operating_cashflow

    return build_item(
        "2. 營業現金流為正",
        None if operating_cashflow is None else operating_cashflow > 0,
        operating_cashflow,
        None,
        "current operating_cashflow > 0 加 1 分",
    )


def evaluate_roa_improvement(current: FinancialPeriod, previous: FinancialPeriod | None) -> dict:
    current_roa = ratio_percent(current.net_income, current.total_assets)
    previous_roa = ratio_percent(previous.net_income, previous.total_assets) if previous else None

    return build_item(
        "3. ROA 較去年提升",
        pass_if_available(current_roa, previous_roa, lambda current_value, previous_value: current_value > previous_value),
        current_roa,
        previous_roa,
        "current ROA > previous ROA 加 1 分",
    )


def evaluate_cashflow_greater_than_net_income(current: FinancialPeriod) -> dict:
    return build_item(
        "4. 營業現金流大於淨利",
        pass_if_available(
            current.operating_cashflow,
            current.net_income,
            lambda current_value, previous_value: current_value > previous_value,
        ),
        current.operating_cashflow,
        current.net_income,
        "current operating_cashflow > current net_income 加 1 分",
    )


def evaluate_long_term_debt_ratio_decline(current: FinancialPeriod, previous: FinancialPeriod | None) -> dict:
    current_ratio = safe_divide(current.long_term_debt, current.total_assets, precision=4)
    previous_ratio = safe_divide(previous.long_term_debt, previous.total_assets, precision=4) if previous else None

    return build_item(
        "5. 長期負債比下降",
        pass_if_available(current_ratio, previous_ratio, lambda current_value, previous_value: current_value < previous_value),
        current_ratio,
        previous_ratio,
        "current long_term_debt / total_assets < previous long_term_debt / total_assets 加 1 分",
    )


def evaluate_current_ratio_improvement(current: FinancialPeriod, previous: FinancialPeriod | None) -> dict:
    current_ratio = safe_divide(current.current_assets, current.current_liabilities)
    previous_ratio = safe_divide(previous.current_assets, previous.current_liabilities) if previous else None

    return build_item(
        "6. 流動比率提升",
        pass_if_available(current_ratio, previous_ratio, lambda current_value, previous_value: current_value > previous_value),
        current_ratio,
        previous_ratio,
        "current current_ratio > previous current_ratio 加 1 分",
    )


def evaluate_no_share_dilution(current: FinancialPeriod, previous: FinancialPeriod | None) -> dict:
    previous_shares = previous.shares_outstanding if previous else None

    return build_item(
        "7. 股本未稀釋",
        pass_if_available(
            current.shares_outstanding,
            previous_shares,
            lambda current_value, previous_value: current_value <= previous_value,
        ),
        current.shares_outstanding,
        previous_shares,
        "current shares_outstanding <= previous shares_outstanding 加 1 分",
    )


def evaluate_gross_margin_improvement(current: FinancialPeriod, previous: FinancialPeriod | None) -> dict:
    current_margin = safe_divide(current.gross_profit, current.revenue, precision=4)
    previous_margin = safe_divide(previous.gross_profit, previous.revenue, precision=4) if previous else None

    return build_item(
        "8. 毛利率提升",
        pass_if_available(current_margin, previous_margin, lambda current_value, previous_value: current_value > previous_value),
        current_margin,
        previous_margin,
        "current gross_profit / revenue > previous gross_profit / revenue 加 1 分",
    )


def evaluate_asset_turnover_improvement(current: FinancialPeriod, previous: FinancialPeriod | None) -> dict:
    current_turnover = safe_divide(current.revenue, current.total_assets, precision=4)
    previous_turnover = safe_divide(previous.revenue, previous.total_assets, precision=4) if previous else None

    return build_item(
        "9. 資產週轉率提升",
        pass_if_available(
            current_turnover,
            previous_turnover,
            lambda current_value, previous_value: current_value > previous_value,
        ),
        current_turnover,
        previous_turnover,
        "current revenue / total_assets > previous revenue / total_assets 加 1 分",
    )
