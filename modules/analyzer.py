def safe_get(info: dict, key: str, default=None):
    value = info.get(key, default)
    return value if value is not None else default


def pct(value):
    if value is None:
        return None
    return round(value * 100, 2)


def calc_piotroski(result: dict) -> dict:
    items = []

    def add(name, passed, note):
        items.append({
            "name": name,
            "passed": passed,
            "note": note,
        })

    add("1. ROA 為正", result["roa"] is not None and result["roa"] > 0, "ROA > 0 加 1 分")
    add("2. 營業現金流為正", result["operating_cashflow"] is not None and result["operating_cashflow"] > 0, "CFO > 0 加 1 分")
    add("3. ROA 較去年提升", None, "v0.4 加入年度比較")
    add("4. 營業現金流大於淨利", None, "v0.4 加入")
    add("5. 長期負債比下降", None, "v0.4 加入")
    add("6. 流動比率提升", None, "v0.4 加入")
    add("7. 股本未稀釋", None, "v0.4 加入")
    add("8. 毛利率提升", None, "v0.4 加入")
    add("9. 資產週轉率提升", None, "v0.4 加入")

    score = sum(1 for item in items if item["passed"] is True)
    available = sum(1 for item in items if item["passed"] is not None)

    return {
        "score": score,
        "available": available,
        "items": items,
    }


def analyze_stock(data: dict) -> dict:
    info = data["info"]
    symbol = data["symbol"]

    company_name = safe_get(info, "longName", "未知公司")
    industry = safe_get(info, "industry", "未知產業")
    sector = safe_get(info, "sector", "未知類別")

    price = safe_get(info, "currentPrice")
    pe = safe_get(info, "trailingPE")
    pb = safe_get(info, "priceToBook")
    roe = pct(safe_get(info, "returnOnEquity"))
    roa = pct(safe_get(info, "returnOnAssets"))
    debt_to_equity = safe_get(info, "debtToEquity")
    current_ratio = safe_get(info, "currentRatio")
    free_cashflow = safe_get(info, "freeCashflow")
    operating_cashflow = safe_get(info, "operatingCashflow")

    result = {
        "symbol": symbol,
        "company_name": company_name,
        "industry": industry,
        "sector": sector,
        "price": price,
        "pe": pe,
        "pb": pb,
        "roe": roe,
        "roa": roa,
        "debt_to_equity": debt_to_equity,
        "current_ratio": current_ratio,
        "free_cashflow": free_cashflow,
        "operating_cashflow": operating_cashflow,
    }

    piotroski = calc_piotroski(result)

    score = 0
    reasons = []

    score += piotroski["score"] * 5
    reasons.append(f"Piotroski 目前可計算 {piotroski['score']} / {piotroski['available']} 項通過")

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

    if free_cashflow is not None and free_cashflow > 0:
        score += 15
        reasons.append("自由現金流為正")
    else:
        reasons.append("自由現金流不佳或資料不足")

    if operating_cashflow is not None and operating_cashflow > 0:
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

    if pe is not None:
        if pe < 15:
            score += 10
            reasons.append("本益比偏低")
        elif pe < 25:
            score += 6
            reasons.append("本益比合理")
        else:
            reasons.append("本益比偏高")

    if pb is not None:
        if pb < 2:
            score += 5
            reasons.append("股價淨值比偏低")
        elif pb < 4:
            score += 3
            reasons.append("股價淨值比合理")

    score = min(score, 100)

    if score >= 90:
        grade = "S級 ⭐⭐⭐⭐⭐"
    elif score >= 80:
        grade = "A級 ⭐⭐⭐⭐"
    elif score >= 70:
        grade = "B級 ⭐⭐⭐"
    elif score >= 60:
        grade = "C級 ⭐⭐"
    else:
        grade = "D級 ⭐"

    result.update({
        "sap_score": score,
        "grade": grade,
        "reasons": reasons,
        "piotroski": piotroski,
    })

    return result
