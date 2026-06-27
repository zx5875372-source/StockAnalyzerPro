from models.financial_data import FinancialData
from modules.growth import calculate_growth
from modules.piotroski import calculate_piotroski
from modules.scoring import calculate_sap_score
from modules.valuation import calculate_valuation


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

    valuation = calculate_valuation(data)
    growth = calculate_growth(data)
    diagnostics = data.diagnostics + valuation["diagnostics"] + growth["diagnostics"]

    provider_metadata = extract_provider_metadata(data.diagnostics)

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
        "diagnostics": diagnostics,
        "provider_source": provider_metadata["provider_source"],
        "provider_selected_provider": provider_metadata["provider_selected_provider"],
        "provider_fallback_used": provider_metadata["provider_fallback_used"],
        "provider_fallback_reason": provider_metadata["provider_fallback_reason"],
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
    scoring = calculate_sap_score(data, piotroski, valuation, growth)

    result.update({
        "sap_score": scoring["total_score"],
        "grade": scoring["grade"],
        "reasons": scoring["reasons"],
        "piotroski": piotroski,
        "valuation": valuation,
        "growth": growth,
        "scoring": scoring,
    })

    return result


def extract_provider_metadata(diagnostics: list[str]) -> dict:
    metadata = {
        "provider_source": "未知",
        "provider_selected_provider": "",
        "provider_fallback_used": False,
        "provider_fallback_reason": "",
    }
    for item in diagnostics:
        if item.startswith("provider_source:"):
            metadata["provider_source"] = item.split(":", 1)[1].strip()
        elif item.startswith("provider_selected_provider:"):
            metadata["provider_selected_provider"] = item.split(":", 1)[1].strip()
        elif item.startswith("provider_fallback_used:"):
            metadata["provider_fallback_used"] = item.split(":", 1)[1].strip().lower() == "true"
        elif item.startswith("provider_fallback_reason:"):
            reason = item.split(":", 1)[1].strip()
            metadata["provider_fallback_reason"] = "" if reason == "-" else reason
    return metadata
