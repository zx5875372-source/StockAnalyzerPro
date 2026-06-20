from models.financial_data import FinancialData, safe_divide


def calculate_growth(data: FinancialData) -> dict:
    current = data.current
    previous = data.previous
    diagnostics = []

    items = [
        score_revenue_growth(current.revenue, previous.revenue if previous else None, diagnostics),
        score_eps_growth(current.eps, previous.eps if previous else None, diagnostics),
        score_fcf_growth(current.free_cashflow, previous.free_cashflow if previous else None, diagnostics),
    ]

    return {
        "score": sum(item["score"] for item in items),
        "max": 13,
        "items": items,
        "diagnostics": diagnostics,
    }


def build_item(name: str, growth_rate: float | None, score: int, max_score: int, note: str) -> dict:
    return {
        "name": name,
        "growth_rate": growth_rate,
        "score": score,
        "max": max_score,
        "note": note,
    }


def growth_rate(current_value: float | None, previous_value: float | None) -> float | None:
    if current_value is None or previous_value is None:
        return None
    return safe_divide(current_value - previous_value, previous_value, precision=4)


def fcf_growth_rate(current_value: float | None, previous_value: float | None) -> float | None:
    if current_value is None or previous_value in (None, 0):
        return None
    return safe_divide(current_value - previous_value, abs(previous_value), precision=4)


def score_revenue_growth(current_revenue: float | None, previous_revenue: float | None, diagnostics: list[str]) -> dict:
    rate = growth_rate(current_revenue, previous_revenue)
    if rate is None:
        diagnostics.append("成長性缺少 current.revenue 或 previous.revenue，營收成長不加分")
        return build_item("營收成長", None, 0, 5, "資料不足，不加分")

    if rate >= 0.10:
        return build_item("營收成長", rate, 5, 5, "營收成長 >= 10%，加 5 分")
    if rate >= 0.05:
        return build_item("營收成長", rate, 3, 5, "營收成長 >= 5%，加 3 分")
    if rate > 0:
        return build_item("營收成長", rate, 1, 5, "營收成長 > 0%，加 1 分")
    return build_item("營收成長", rate, 0, 5, "營收未成長，不加分")


def score_eps_growth(current_eps: float | None, previous_eps: float | None, diagnostics: list[str]) -> dict:
    rate = growth_rate(current_eps, previous_eps)
    if rate is None:
        diagnostics.append("成長性缺少 current.eps 或 previous.eps，EPS 成長不加分")
        return build_item("EPS 成長", None, 0, 5, "資料不足，不加分")

    if rate >= 0.10:
        return build_item("EPS 成長", rate, 5, 5, "EPS 成長 >= 10%，加 5 分")
    if rate >= 0.05:
        return build_item("EPS 成長", rate, 3, 5, "EPS 成長 >= 5%，加 3 分")
    if rate > 0:
        return build_item("EPS 成長", rate, 1, 5, "EPS 成長 > 0%，加 1 分")
    return build_item("EPS 成長", rate, 0, 5, "EPS 未成長，不加分")


def score_fcf_growth(current_fcf: float | None, previous_fcf: float | None, diagnostics: list[str]) -> dict:
    rate = fcf_growth_rate(current_fcf, previous_fcf)
    if rate is None:
        diagnostics.append("成長性缺少 current.free_cashflow 或 previous.free_cashflow，FCF 成長不加分")
        return build_item("自由現金流成長", None, 0, 3, "資料不足，不加分")

    if rate > 0:
        return build_item("自由現金流成長", rate, 3, 3, "自由現金流成長 > 0%，加 3 分")
    return build_item("自由現金流成長", rate, 0, 3, "自由現金流未成長，不加分")
