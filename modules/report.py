from pathlib import Path
from datetime import datetime


def fmt(value, suffix=""):
    if value is None:
        return "資料不足"
    return f"{value}{suffix}"


def metric(value):
    if value is None:
        return "資料不足"
    if isinstance(value, (int, float)):
        if abs(value) >= 100000:
            return f"{value:,.0f}"
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def percent(value):
    if value is None:
        return "資料不足"
    return f"{round(value * 100, 2)}%"


def money(value):
    if value is None:
        return "資料不足"
    return f"{value:,.0f}"


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


def generate_markdown_report(result: dict) -> str:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    symbol = result["symbol"]
    today = datetime.now().strftime("%Y%m%d")
    path = reports_dir / f"{symbol}_{today}.md"

    reasons_text = "\n".join([f"- {r}" for r in result["reasons"]])
    diagnostics = result.get("diagnostics") or ["無明顯缺漏"]
    diagnostics_text = "\n".join([f"- {item}" for item in diagnostics])

    piotroski = result.get("piotroski", {"score": 0, "available": 0, "items": []})
    piotroski_total = piotroski.get("total", 9)
    valuation = result.get("valuation", {})
    growth = result.get("growth", {"score": 0, "max": 13, "items": []})
    scoring = result.get("scoring", {"categories": {}})
    scoring_categories = default_scoring_categories()
    scoring_categories.update(scoring.get("categories", {}))
    scoring_rows = scoring_item_rows(scoring_categories)
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
| 產業 | {result["industry"]} |
| 類別 | {result["sector"]} |
| 目前股價 | {fmt(result["price"])} |
| 最新財報期 | {fmt(result["current_period"])} |
| 前一財報期 | {fmt(result["previous_period"])} |

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

## 十一、資料缺漏診斷

{diagnostics_text}

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

目前版本為 SAP v1.1 Validation & Backtesting Foundation。

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
