from models.financial_data import FinancialData
from valuation.valuation_profiles import get_valuation_profile


def calculate_valuation(data: FinancialData) -> dict:
    eps = data.current.eps
    book_value_per_share = data.current.book_value_per_share
    diagnostics = []
    profile, mapping = get_valuation_profile(data.industry, data.sector)
    reasonable_pe = profile.target_pe
    reasonable_pb = profile.target_pb

    diagnostics.extend(
        [
            f"valuation_profile: {profile.name}",
            f"valuation_source: {profile.source}",
            f"industry_mapping: industry={mapping['industry']}, sector={mapping['sector']}, profile={profile.name}",
        ]
    )

    if eps is None:
        diagnostics.append("估值缺少 current.eps")
    elif eps <= 0:
        diagnostics.append("估值 current.eps 非正值，暫不計算 PE 合理價")

    if book_value_per_share is None:
        diagnostics.append("估值缺少 current.book_value_per_share")
    elif book_value_per_share <= 0:
        diagnostics.append("估值 current.book_value_per_share 非正值，暫不計算 PB 合理價")

    pe_fair_price = round(eps * reasonable_pe, 2) if eps is not None and eps > 0 else None
    pb_fair_price = (
        round(book_value_per_share * reasonable_pb, 2)
        if book_value_per_share is not None and book_value_per_share > 0
        else None
    )

    fair_price = None
    if pe_fair_price is not None and pb_fair_price is not None:
        fair_price = round((pe_fair_price + pb_fair_price) / 2, 2)
    else:
        diagnostics.append("估值缺少 PE 合理價或 PB 合理價，無法計算綜合合理價")

    conservative_buy = round(fair_price * 0.75, 2) if fair_price is not None else None
    reasonable_buy = round(fair_price * 0.85, 2) if fair_price is not None else None
    aggressive_buy = round(fair_price * 0.95, 2) if fair_price is not None else None
    first_target_price = round(fair_price * 1.15, 2) if fair_price is not None else None

    upside_percent = None
    if first_target_price is not None and data.price is not None and data.price > 0:
        upside_percent = round((first_target_price / data.price - 1) * 100, 2)
    elif first_target_price is not None:
        diagnostics.append("估值缺少目前股價，無法計算預估上漲空間")

    return {
        "reasonable_pe": reasonable_pe,
        "reasonable_pb": reasonable_pb,
        "valuation_profile": profile.name,
        "valuation_source": profile.source,
        "industry_mapping": mapping,
        "pe_range": (profile.pe_min, profile.pe_max),
        "pb_range": (profile.pb_min, profile.pb_max),
        "eps": eps,
        "book_value_per_share": book_value_per_share,
        "pe_fair_price": pe_fair_price,
        "pb_fair_price": pb_fair_price,
        "fair_price": fair_price,
        "conservative_buy": conservative_buy,
        "reasonable_buy": reasonable_buy,
        "aggressive_buy": aggressive_buy,
        "first_target_price": first_target_price,
        "upside_percent": upside_percent,
        "diagnostics": diagnostics,
    }
