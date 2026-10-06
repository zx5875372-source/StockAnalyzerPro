from modules.report.formatters import (
    compact_metric,
    format_currency,
    format_percent,
    format_ratio,
    range_text,
    translate_industry,
)


def piotroski_value(item: dict, field_name: str) -> str:
    value = item.get(field_name)
    if value is None:
        return "資料不足"
    item_name = item.get("name")
    if item_name in {"1. ROA 為正", "3. ROA 較去年提升"}:
        return format_percent(value, value_is_ratio=False)
    if item_name in {"5. 長期負債比下降", "8. 毛利率提升"}:
        return format_percent(value, value_is_ratio=True)
    if item_name in {"6. 流動比率提升", "9. 資產週轉率提升"}:
        return format_ratio(value)
    return format_currency(value)


def piotroski_comparison_value(item: dict) -> str:
    if item.get("name") in {
        "1. ROA 為正",
        "2. 營業現金流為正",
    }:
        return "不適用"
    return piotroski_value(item, "previous_value")


def scoring_item_rows(categories: dict) -> str:
    category_names = {
        "piotroski": "Piotroski F-Score",
        "profitability": "獲利能力",
        "financial_health": "財務體質",
        "cashflow": "現金流",
        "valuation": "估值",
        "growth": "成長性",
    }
    rows = []

    for key, category in categories.items():
        category_name = category_names.get(key, key)
        for item in category["items"]:
            if isinstance(item, dict):
                rows.append(
                    f"| {category_name} | {item['name']} | {item['score']} / {item['max']} | {item['note']} |"
                )
            else:
                rows.append(f"| {category_name} | {item} | 0 / {category['max']} | 後續版本加入 |")

    return "\n".join(rows)


def default_scoring_categories() -> dict:
    return {
        "piotroski": {"score": 0, "max": 27, "items": []},
        "profitability": {"score": 0, "max": 20, "items": []},
        "financial_health": {"score": 0, "max": 15, "items": []},
        "cashflow": {"score": 0, "max": 15, "items": []},
        "valuation": {"score": 0, "max": 10, "items": []},
        "growth": {"score": 0, "max": 13, "items": []},
    }


def plain_language_judgement(result: dict) -> dict:
    grade = str(result.get("grade", "")).strip().upper().replace("級", "")
    if grade in {"S", "A"}:
        summary = "可優先研究。"
    elif grade == "B":
        summary = "可觀察，需等合理買點。"
    elif grade == "C":
        summary = "保守觀察。"
    else:
        summary = "目前不建議買進。"

    reasons = []
    sap_score = result.get("sap_score")
    if sap_score is not None and sap_score < 60:
        reasons.append("SAP 評分偏低，整體基本面仍需改善。")
    elif sap_score is not None and sap_score >= 80:
        reasons.append("SAP 評分較高，基本面可優先研究。")
    if result.get("free_cashflow") is not None and result.get("free_cashflow") < 0:
        reasons.append("自由現金流為負，需特別注意。")
    if result.get("operating_cashflow") is not None and result.get("operating_cashflow") < 0:
        reasons.append("營業現金流為負，需特別注意。")

    valuation = result.get("valuation", {})
    price = result.get("price")
    first_target_price = valuation.get("first_target_price")
    upside_percent = valuation.get("upside_percent")
    if price is not None and first_target_price is not None and price > first_target_price:
        reasons.append("目前股價高於第一目標價，追價風險偏高。")
    if upside_percent is not None and upside_percent < 0:
        reasons.append("預估上漲空間為負，代表目前價格高於模型估算目標價。")
    if result.get("pe_judgement") == "偏高" or result.get("pb_judgement") == "偏高":
        reasons.append("PE / PB 偏高，估值不便宜。")
    if not reasons:
        reasons.append("目前沒有明顯重大警訊，但仍需搭配產業與風險評估。")

    return {"summary": summary, "reasons": reasons}


def valuation_warnings(result: dict) -> str:
    valuation = result.get("valuation", {})
    warnings = []
    price = result.get("price")
    first_target_price = valuation.get("first_target_price")
    upside_percent = valuation.get("upside_percent")
    if price is not None and first_target_price is not None and price > first_target_price:
        warnings.append("⚠ 目前股價已高於第一目標價，追價風險偏高。")
    if upside_percent is not None and upside_percent < 0:
        warnings.append("預估上漲空間為負，代表目前價格高於模型估算目標價。")
    return "\n".join(warnings) if warnings else "無明顯估值警示。"


def valuation_model_text(valuation: dict) -> dict:
    return {
        "profile": valuation.get("valuation_profile") or "傳產",
        "pe_range": range_text(valuation.get("pe_range")),
        "pb_range": range_text(valuation.get("pb_range")),
        "reasonable_pe": compact_metric(valuation.get("reasonable_pe")),
        "reasonable_pb": compact_metric(valuation.get("reasonable_pb")),
    }


def technical_result(result: dict) -> dict:
    technical = dict(result.get("technical") or {})
    defaults = {
        "trend_score": None,
        "technical_grade": "資料不足",
        "ma20": None,
        "ma60": None,
        "ma120": None,
        "ma240": None,
        "rsi14": None,
        "rsi_status": "資料不足",
        "macd": None,
        "macd_signal": None,
        "macd_histogram": None,
        "macd_status": "資料不足",
        "volume_ratio": None,
        "golden_cross": False,
        "death_cross": False,
        "diagnostics": ["technical_missing_fields: technical_result"],
    }
    defaults.update(technical)
    return defaults


def total_score(sap_score, trend_score) -> float | None:
    if sap_score is None or trend_score is None:
        return None
    return round(float(sap_score) * 0.6 + float(trend_score) * 0.4, 2)


def industry_rank_text(rank, size) -> str:
    if rank in {None, ""} or not size:
        return "資料不足"
    return f"{rank} / {size}"


def industry_ranking_result(result: dict) -> dict:
    ranking = dict(result.get("industry_ranking") or {})
    industry_name = ranking.get("industry_name") or result.get("industry") or "未知產業"
    size = ranking.get("industry_size") or 0
    top_percent = ranking.get("top_percent") or "資料不足"
    return {
        "industry_name": translate_industry(industry_name),
        "industry_size": size or "資料不足",
        "sap_rank": industry_rank_text(ranking.get("sap_rank"), size),
        "trend_rank": industry_rank_text(ranking.get("trend_rank"), size),
        "total_rank": industry_rank_text(ranking.get("total_rank"), size),
        "top_percent": top_percent,
        "rating": ranking.get("rating") or ("資料不足" if top_percent == "資料不足" else "★★★"),
        "summary_text": ranking.get("summary_text") or "產業資料不足，暫無法排名",
    }
