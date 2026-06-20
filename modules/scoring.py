from models.financial_data import FinancialData


def calculate_sap_score(data: FinancialData, piotroski: dict, valuation: dict, growth: dict) -> dict:
    categories = {
        "piotroski": score_piotroski(piotroski),
        "profitability": score_profitability(data),
        "financial_health": score_financial_health(data),
        "cashflow": score_cashflow(data),
        "valuation": score_valuation(data),
        "growth": score_growth(growth),
    }

    total_score = min(sum(category["score"] for category in categories.values()), 100)

    return {
        "total_score": total_score,
        "grade": grade_from_score(total_score),
        "categories": categories,
        "reasons": build_reasons(categories),
    }


def build_item(name: str, score: int, max_score: int, note: str) -> dict:
    return {
        "name": name,
        "score": score,
        "max": max_score,
        "note": note,
    }


def score_piotroski(piotroski: dict) -> dict:
    score = min(piotroski.get("score", 0) * 3, 27)

    return {
        "score": score,
        "max": 27,
        "items": [
            build_item(
                "Piotroski F-Score",
                score,
                27,
                f"{piotroski.get('score', 0)} / {piotroski.get('total', 9)} 通過，每項 3 分",
            )
        ],
    }


def score_profitability(data: FinancialData) -> dict:
    roe = data.roe()
    roa = data.roa()

    roe_score, roe_note = score_roe(roe)
    roa_score, roa_note = score_roa(roa)

    return {
        "score": roe_score + roa_score,
        "max": 20,
        "items": [
            build_item("ROE", roe_score, 12, roe_note),
            build_item("ROA", roa_score, 8, roa_note),
        ],
    }


def score_roe(roe: float | None) -> tuple[int, str]:
    if roe is None:
        return 0, "ROE 資料不足，不加分"
    if roe >= 15:
        return 12, "ROE >= 15%，加 12 分"
    if roe >= 10:
        return 8, "ROE >= 10%，加 8 分"
    if roe >= 5:
        return 4, "ROE >= 5%，加 4 分"
    return 0, "ROE < 5%，不加分"


def score_roa(roa: float | None) -> tuple[int, str]:
    if roa is None:
        return 0, "ROA 資料不足，不加分"
    if roa >= 8:
        return 8, "ROA >= 8%，加 8 分"
    if roa >= 5:
        return 5, "ROA >= 5%，加 5 分"
    if roa >= 2:
        return 2, "ROA >= 2%，加 2 分"
    return 0, "ROA < 2%，不加分"


def score_financial_health(data: FinancialData) -> dict:
    debt_to_equity = data.debt_to_equity()
    current_ratio = data.current_ratio()

    debt_score, debt_note = score_debt_to_equity(debt_to_equity)
    current_ratio_score, current_ratio_note = score_current_ratio(current_ratio)

    return {
        "score": debt_score + current_ratio_score,
        "max": 15,
        "items": [
            build_item("負債權益比", debt_score, 8, debt_note),
            build_item("流動比率", current_ratio_score, 7, current_ratio_note),
        ],
    }


def score_debt_to_equity(debt_to_equity: float | None) -> tuple[int, str]:
    if debt_to_equity is None:
        return 0, "負債權益比資料不足，不加分"
    if debt_to_equity < 80:
        return 8, "負債權益比 < 80%，加 8 分"
    if debt_to_equity < 150:
        return 4, "負債權益比 < 150%，加 4 分"
    return 0, "負債權益比 >= 150%，不加分"


def score_current_ratio(current_ratio: float | None) -> tuple[int, str]:
    if current_ratio is None:
        return 0, "流動比率資料不足，不加分"
    if current_ratio >= 1.5:
        return 7, "流動比率 >= 1.5，加 7 分"
    if current_ratio >= 1:
        return 3, "流動比率 >= 1，加 3 分"
    return 0, "流動比率 < 1，不加分"


def score_cashflow(data: FinancialData) -> dict:
    operating_score = 7 if data.current.operating_cashflow is not None and data.current.operating_cashflow > 0 else 0
    free_score = 8 if data.current.free_cashflow is not None and data.current.free_cashflow > 0 else 0

    return {
        "score": operating_score + free_score,
        "max": 15,
        "items": [
            build_item(
                "營業現金流",
                operating_score,
                7,
                "營業現金流 > 0，加 7 分" if operating_score else "營業現金流不為正或資料不足，不加分",
            ),
            build_item(
                "自由現金流",
                free_score,
                8,
                "自由現金流 > 0，加 8 分" if free_score else "自由現金流不為正或資料不足，不加分",
            ),
        ],
    }


def score_valuation(data: FinancialData) -> dict:
    pe_score = 5 if data.pe is not None and data.pe < 15 else 0
    pb_score = 5 if data.pb is not None and data.pb < 2 else 0

    return {
        "score": pe_score + pb_score,
        "max": 10,
        "items": [
            build_item("PE", pe_score, 5, "PE < 15，加 5 分" if pe_score else "PE >= 15 或資料不足，不加分"),
            build_item("PB", pb_score, 5, "PB < 2，加 5 分" if pb_score else "PB >= 2 或資料不足，不加分"),
        ],
    }


def score_growth(growth: dict) -> dict:
    return {
        "score": growth.get("score", 0),
        "max": 13,
        "items": growth.get("items", []),
    }


def grade_from_score(score: int) -> str:
    if score >= 90:
        return "S級"
    if score >= 80:
        return "A級"
    if score >= 70:
        return "B級"
    if score >= 60:
        return "C級"
    return "D級"


def build_reasons(categories: dict) -> list[str]:
    reasons = []

    for category in categories.values():
        for item in category["items"]:
            if isinstance(item, dict):
                reasons.append(f"{item['name']}：{item['note']}")
            else:
                reasons.append(str(item))

    return reasons
