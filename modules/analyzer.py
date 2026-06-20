from models.financial_data import FinancialData
from modules.piotroski import calculate_piotroski


def judge_roe(roe: float | None) -> str:
    if roe is None:
        return "資料不足"
    if roe >= 15:
        return "佳"
    if roe >= 5:
        return "普通"
    return "需觀察"


def judge_roa(roa: float | None) -> str:
    if roa is None:
        return "資料不足"
    if roa >= 8:
        return "佳"
    if roa >= 2:
        return "普通"
    return "需觀察"


def judge_debt_to_equity(debt_to_equity: float | None) -> str:
    if debt_to_equity is None:
        return "資料不足"
    if debt_to_equity < 80:
        return "安全"
    if debt_to_equity < 150:
        return "中等"
    return "需觀察"


def judge_current_ratio(current_ratio: float | None) -> str:
    if current_ratio is None:
        return "資料不足"
    if current_ratio >= 1.5:
        return "良好"
    if current_ratio >= 1:
        return "普通"
    return "需觀察"


def judge_cashflow(value: float | None) -> str:
    if value is None:
        return "資料不足"
    if value > 0:
        return "正向"
    return "需觀察"


def judge_pe(pe: float | None) -> str:
    if pe is None:
        return "資料不足"
    if pe < 15:
        return "偏低"
    if pe < 25:
        return "合理"
    return "偏高"


def judge_pb(pb: float | None) -> str:
    if pb is None:
        return "資料不足"
    if pb < 2:
        return "偏低"
    if pb < 4:
        return "合理"
    return "偏高"


def analyze_stock(data: FinancialData) -> dict:
    roe = data.roe()
    roa = data.roa()
    debt_to_equity = data.debt_to_equity()
    current_ratio = data.current_ratio()

    result = {
        "symbol": data.symbol,
        "company_name": data.company_name or "未知公司",
        "industry": data.industry or "未知產業",
        "sector": data.sector or "未知類別",
        "price": data.price,
        "current_period": data.current.period,
        "previous_period": data.previous.period if data.previous else None,
        "pe": data.pe,
        "pb": data.pb,
        "roe": roe,
        "roa": roa,
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "free_cashflow": data.current.free_cashflow,
        "operating_cashflow": data.current.operating_cashflow,
        "missing_fields": data.missing_fields,
        "diagnostics": data.diagnostics,
        "roe_judgement": judge_roe(roe),
        "roa_judgement": judge_roa(roa),
        "debt_to_equity_judgement": judge_debt_to_equity(debt_to_equity),
        "current_ratio_judgement": judge_current_ratio(current_ratio),
        "operating_cashflow_judgement": judge_cashflow(data.current.operating_cashflow),
        "free_cashflow_judgement": judge_cashflow(data.current.free_cashflow),
        "pe_judgement": judge_pe(data.pe),
        "pb_judgement": judge_pb(data.pb),
    }

    piotroski = calculate_piotroski(data)

    score = 0
    reasons = []

    score += piotroski["score"] * 3
    reasons.append(
        f"Piotroski F-Score {piotroski['score']} / {piotroski['total']}，"
        f"可計算 {piotroski['score']} / {piotroski['available']} 項通過"
    )

    if roe is not None:
        if roe >= 15:
            score += 20
            reasons.append("ROE 高於 15%，獲利能力佳")
        elif roe >= 10:
            score += 14
            reasons.append("ROE 高於 10%，獲利能力尚可")
        elif roe >= 5:
            score += 8
            reasons.append("ROE 偏低但仍為正")
        else:
            reasons.append("ROE 偏弱")

    if roa is not None:
        if roa >= 8:
            score += 15
            reasons.append("ROA 高於 8%，資產運用效率佳")
        elif roa >= 5:
            score += 10
            reasons.append("ROA 尚可")
        elif roa >= 2:
            score += 5
            reasons.append("ROA 偏低")

    if data.current.free_cashflow is not None and data.current.free_cashflow > 0:
        score += 15
        reasons.append("自由現金流為正")
    else:
        reasons.append("自由現金流不佳或資料不足")

    if data.current.operating_cashflow is not None and data.current.operating_cashflow > 0:
        score += 10
        reasons.append("營業現金流為正")

    if debt_to_equity is not None:
        if debt_to_equity < 80:
            score += 15
            reasons.append("負債比相對安全")
        elif debt_to_equity < 150:
            score += 8
            reasons.append("負債比中等")
        else:
            reasons.append("負債偏高")

    if current_ratio is not None:
        if current_ratio >= 1.5:
            score += 10
            reasons.append("流動比率良好")
        elif current_ratio >= 1:
            score += 5
            reasons.append("流動比率尚可")

    if data.pe is not None:
        if data.pe < 15:
            score += 10
            reasons.append("本益比偏低")
        elif data.pe < 25:
            score += 6
            reasons.append("本益比合理")
        else:
            reasons.append("本益比偏高")

    if data.pb is not None:
        if data.pb < 2:
            score += 5
            reasons.append("股價淨值比偏低")
        elif data.pb < 4:
            score += 3
            reasons.append("股價淨值比合理")

    score = min(score, 100)

    if score >= 90:
        grade = "S級"
    elif score >= 80:
        grade = "A級"
    elif score >= 70:
        grade = "B級"
    elif score >= 60:
        grade = "C級"
    else:
        grade = "D級"

    result.update({
        "sap_score": score,
        "grade": grade,
        "reasons": reasons,
        "piotroski": piotroski,
    })

    return result
