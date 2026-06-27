from pathlib import Path
from datetime import datetime


INDUSTRY_TRANSLATIONS = {
    "Technology": "科技",
    "Communication Equipment": "通訊設備",
    "Semiconductors": "半導體",
    "Electronic Components": "電子零組件",
    "Computer Hardware": "電腦及週邊設備",
    "Consumer Electronics": "消費性電子",
    "Industrials": "工業",
    "Basic Materials": "原物料",
    "Financial Services": "金融",
    "Healthcare": "醫療保健",
    "Consumer Cyclical": "非必需消費",
    "Consumer Defensive": "民生消費",
    "Utilities": "公用事業",
    "Real Estate": "房地產",
    "Energy": "能源",
}

CRITICAL_MISSING_FIELDS = {
    "current_price",
    "price",
    "current.price",
    "current.eps",
    "eps",
    "current.revenue",
    "revenue",
    "current.net_income",
    "net_income",
    "current.total_assets",
    "total_assets",
}

ADVANCED_DIAGNOSTIC_MARKERS = [
    "unmapped_raw_fields",
    "provider_route",
    "finmind_mapped_fields",
    "mapped_fields:",
    "mapped_fields_count",
    "derived_fields",
    "yahoo_enriched_fields",
    "provider_selected_provider",
    "provider_fallback_used",
    "provider_fallback_reason",
]


def fmt(value, suffix=""):
    if value is None:
        return "資料不足"
    if isinstance(value, (int, float)):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def metric(value):
    if value is None:
        return "資料不足"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}"
    return str(value)


def percent(value):
    if value is None:
        return "資料不足"
    return f"{round(value * 100, 2)}%"


def money(value):
    if value is None:
        return "資料不足"
    return f"{value:,.2f}"


def yes_no(value):
    if value is True:
        return "通過"
    if value is False:
        return "未通過"
    return "資料不足"


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


def translate_industry(value) -> str:
    if value in {None, ""}:
        return "資料不足"
    return INDUSTRY_TRANSLATIONS.get(str(value), str(value))


def data_completeness_summary(result: dict) -> dict:
    missing_fields = extract_still_missing_fields(result)
    if result.get("price") is None:
        missing_fields.append("current_price")

    unique_missing_fields = sorted(set(missing_fields))
    missing_text = "無" if not unique_missing_fields else ", ".join(unique_missing_fields)
    has_critical_missing = any(field in CRITICAL_MISSING_FIELDS for field in unique_missing_fields)

    if not unique_missing_fields:
        status = "完整"
    elif has_critical_missing:
        status = "資料不足"
    else:
        status = "部分缺漏"

    return {
        "status": status,
        "primary_source": primary_source(result),
        "supplement_source": supplement_source(result),
        "missing_text": missing_text,
    }


def extract_still_missing_fields(result: dict) -> list[str]:
    fields = []
    for item in result.get("diagnostics", []):
        if not item.startswith("still_missing_fields:"):
            continue
        value = item.split(":", 1)[1].strip()
        if value and value != "-":
            fields.extend([field.strip() for field in value.split(",") if field.strip()])
    if fields:
        return fields
    return list(result.get("missing_fields", []))


def primary_source(result: dict) -> str:
    provider_source = result.get("provider_source") or "未知"
    if "fallback" in provider_source:
        return "Yahoo Finance"
    if "Yahoo" in provider_source:
        return "Yahoo Finance"
    if "FinMind" in provider_source:
        return "FinMind"
    return provider_source


def supplement_source(result: dict) -> str:
    diagnostics = result.get("diagnostics", [])
    if primary_source(result) == "FinMind" and any(
        item.startswith("yahoo_enriched_fields:") and item.split(":", 1)[1].strip() != "-"
        for item in diagnostics
    ):
        return "Yahoo Finance"
    if result.get("provider_fallback_used"):
        return "FinMind fallback"
    return "無"


def split_diagnostics(diagnostics: list[str]) -> tuple[list[str], list[str]]:
    general = []
    advanced = []
    for item in diagnostics:
        if is_advanced_diagnostic(item):
            advanced.append(item)
        else:
            general.append(item)
    return general or ["無明顯缺漏"], advanced or ["無"]


def is_advanced_diagnostic(item: str) -> bool:
    return any(marker in item for marker in ADVANCED_DIAGNOSTIC_MARKERS)


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


def numbered_lines(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


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


def generate_markdown_report(result: dict) -> str:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    symbol = result["symbol"]
    today = datetime.now().strftime("%Y%m%d")
    path = reports_dir / f"{symbol}_{today}.md"

    reasons_text = "\n".join([f"- {r}" for r in result["reasons"]])
    diagnostics = result.get("diagnostics") or ["無明顯缺漏"]
    general_diagnostics, advanced_diagnostics = split_diagnostics(diagnostics)
    general_diagnostics_text = "\n".join([f"- {item}" for item in general_diagnostics])
    advanced_diagnostics_text = "\n".join([f"- {item}" for item in advanced_diagnostics])

    piotroski = result.get("piotroski", {"score": 0, "available": 0, "items": []})
    piotroski_total = piotroski.get("total", 9)
    valuation = result.get("valuation", {})
    growth = result.get("growth", {"score": 0, "max": 13, "items": []})
    scoring = result.get("scoring", {"categories": {}})
    scoring_categories = default_scoring_categories()
    scoring_categories.update(scoring.get("categories", {}))
    scoring_rows = scoring_item_rows(scoring_categories)
    fallback_text = "是" if result.get("provider_fallback_used") else "否"
    fallback_reason = result.get("provider_fallback_reason") or "-"
    completeness = data_completeness_summary(result)
    plain_judgement = plain_language_judgement(result)
    plain_judgement_reasons = numbered_lines(plain_judgement["reasons"])
    valuation_warning_text = valuation_warnings(result)
    piotroski_rows = "\n".join(
        [
            "| "
            f"{item['name']} | "
            f"{yes_no(item['passed'])} | "
            f"{metric(item.get('current_value'))} | "
            f"{metric(item.get('previous_value'))} | "
            f"{item['note']} |"
            for item in piotroski["items"]
        ]
    )

    content = f"""# {symbol} 固定格式股票分析報告

## 一、公司基本資料

| 項目 | 內容 |
|---|---|
| 股票代號 | {result["symbol"]} |
| 公司名稱 | {result["company_name"]} |
| 產業 | {translate_industry(result["industry"])} |
| 類別 | {translate_industry(result["sector"])} |
| 目前股價 | {fmt(result["price"])} |
| 最新財報期 | {fmt(result["current_period"])} |
| 前一財報期 | {fmt(result["previous_period"])} |
| 資料來源 | {result.get("provider_source", "未知")} |
| Fallback | {fallback_text} |
| Fallback 原因 | {fallback_reason} |

資料來源：{result.get("provider_source", "未知")}

Fallback：{fallback_text}

---

## 資料完整度摘要

| 項目 | 結果 |
|---|---|
| 資料完整度 | {completeness["status"]} |
| 主要資料來源 | {completeness["primary_source"]} |
| 補充資料來源 | {completeness["supplement_source"]} |
| 目前缺漏欄位 | {completeness["missing_text"]} |

---

## 二、Piotroski F-Score

| 項目 | 結果 |
|---|---:|
| 完整分數 | {piotroski["score"]} / {piotroski_total} |
| 可計算項目 | {piotroski["score"]} / {piotroski["available"]} |

| 細項 | 結果 | 目前值 | 去年值/比較值 | 說明 |
|---|---|---:|---:|---|
{piotroski_rows}

---

## 三、獲利能力

| 指標 | 數值 | 判斷 |
|---|---:|---|
| ROE | {fmt(result["roe"], "%")} | {result["roe_judgement"]} |
| ROA | {fmt(result["roa"], "%")} | {result["roa_judgement"]} |

---

## 四、財務體質

| 指標 | 數值 | 判斷 |
|---|---:|---|
| 負債權益比 | {fmt(result["debt_to_equity"], "%")} | {result["debt_to_equity_judgement"]} |
| 流動比率 | {fmt(result["current_ratio"])} | {result["current_ratio_judgement"]} |

---

## 五、現金流

| 指標 | 數值 | 判斷 |
|---|---:|---|
| 營業現金流 | {money(result["operating_cashflow"])} | {result["operating_cashflow_judgement"]} |
| 自由現金流 | {money(result["free_cashflow"])} | {result["free_cashflow_judgement"]} |

---

## 六、成長性

| 項目 | 成長率 | 分數 | 判斷 |
|---|---:|---:|---|
| 營收成長 | {percent(growth["items"][0]["growth_rate"]) if len(growth["items"]) > 0 else "資料不足"} | {growth["items"][0]["score"] if len(growth["items"]) > 0 else 0} / {growth["items"][0]["max"] if len(growth["items"]) > 0 else 5} | {growth["items"][0]["note"] if len(growth["items"]) > 0 else "資料不足"} |
| EPS 成長 | {percent(growth["items"][1]["growth_rate"]) if len(growth["items"]) > 1 else "資料不足"} | {growth["items"][1]["score"] if len(growth["items"]) > 1 else 0} / {growth["items"][1]["max"] if len(growth["items"]) > 1 else 5} | {growth["items"][1]["note"] if len(growth["items"]) > 1 else "資料不足"} |
| 自由現金流成長 | {percent(growth["items"][2]["growth_rate"]) if len(growth["items"]) > 2 else "資料不足"} | {growth["items"][2]["score"] if len(growth["items"]) > 2 else 0} / {growth["items"][2]["max"] if len(growth["items"]) > 2 else 3} | {growth["items"][2]["note"] if len(growth["items"]) > 2 else "資料不足"} |

---

## 七、估值

| 指標 | 數值 | 判斷 |
|---|---:|---|
| 本益比 PE | {fmt(result["pe"])} | {result["pe_judgement"]} |
| 股價淨值比 PB | {fmt(result["pb"])} | {result["pb_judgement"]} |
| EPS | {metric(valuation.get("eps"))} | 估值輸入 |
| 每股淨值 | {metric(valuation.get("book_value_per_share"))} | 估值輸入 |
| 合理 PE | {metric(valuation.get("reasonable_pe"))} | v1.0 固定假設 |
| 合理 PB | {metric(valuation.get("reasonable_pb"))} | v1.0 固定假設 |
| PE 合理價 | {metric(valuation.get("pe_fair_price"))} | EPS × 合理 PE |
| PB 合理價 | {metric(valuation.get("pb_fair_price"))} | 每股淨值 × 合理 PB |
| 綜合合理價 | {metric(valuation.get("fair_price"))} | PE/PB 合理價平均 |

### 估值警示

{valuation_warning_text}

---

## 八、動態買點區間

| 項目 | 結果 |
|---|---|
| 保守買點 | {metric(valuation.get("conservative_buy"))} |
| 合理買點 | {metric(valuation.get("reasonable_buy"))} |
| 積極買點 | {metric(valuation.get("aggressive_buy"))} |

---

## 九、第一目標價

| 項目 | 結果 |
|---|---|
| 第一目標價 | {metric(valuation.get("first_target_price"))} |
| 預估上漲空間 | {fmt(valuation.get("upside_percent"), "%")} |

---

## 十、風險分析

目前風險判斷：

{reasons_text}

---

## 十一、資料完整度與診斷

### 一般診斷

{general_diagnostics_text}

### 進階診斷

{advanced_diagnostics_text}

---

## 十二、細項評分

| 項目 | 分數 |
|---|---:|
| Piotroski 完整分數 | {piotroski["score"]} / {piotroski_total} |
| Piotroski 可計算項目 | {piotroski["score"]} / {piotroski["available"]} |
| SAP Score | {result["sap_score"]} / 100 |
| 投資等級 | {result["grade"]} |

| 大類 | 分數 |
|---|---:|
| Piotroski F-Score | {scoring_categories["piotroski"]["score"]} / {scoring_categories["piotroski"]["max"]} |
| 獲利能力 | {scoring_categories["profitability"]["score"]} / {scoring_categories["profitability"]["max"]} |
| 財務體質 | {scoring_categories["financial_health"]["score"]} / {scoring_categories["financial_health"]["max"]} |
| 現金流 | {scoring_categories["cashflow"]["score"]} / {scoring_categories["cashflow"]["max"]} |
| 估值 | {scoring_categories["valuation"]["score"]} / {scoring_categories["valuation"]["max"]} |
| 成長性 | {scoring_categories["growth"]["score"]} / {scoring_categories["growth"]["max"]} |

| 大類 | 項目 | 分數 | 加分原因 |
|---|---|---:|---|
{scoring_rows}

---

## 十三、投資建議

目前版本為 StockAnalyzerPro v3.0 FinMind First Beta。

### 白話判斷

{plain_judgement["summary"]}

原因：

{plain_judgement_reasons}

### 評分摘要

初步判斷：

- Piotroski 完整分數：{piotroski["score"]} / {piotroski_total}
- Piotroski 可計算項目：{piotroski["score"]} / {piotroski["available"]}
- SAP Score：{result["sap_score"]} / 100
- 投資等級：{result["grade"]}
- 成長性分數：{growth.get("score", 0)} / {growth.get("max", 13)}
- 綜合合理價：{metric(valuation.get("fair_price"))}
- 第一目標價：{metric(valuation.get("first_target_price"))}

Piotroski 明細使用 current / previous 財報資料計算；資料不足的項目不計入可計算項目。

"""

    path.write_text(content, encoding="utf-8")
    return str(path)
