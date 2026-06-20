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

| 項目 | 結果 |
|---|---|
| 營收成長 | 後續版本加入 |
| EPS 成長 | 後續版本加入 |
| 自由現金流成長 | 後續版本加入 |

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

---

## 十三、投資建議

目前版本為 SAP v0.7，已加入 Valuation Engine v1.0。

初步判斷：

- Piotroski 完整分數：{piotroski["score"]} / {piotroski_total}
- Piotroski 可計算項目：{piotroski["score"]} / {piotroski["available"]}
- SAP Score：{result["sap_score"]} / 100
- 投資等級：{result["grade"]}
- 綜合合理價：{metric(valuation.get("fair_price"))}
- 第一目標價：{metric(valuation.get("first_target_price"))}

Piotroski 明細使用 current / previous 財報資料計算；資料不足的項目不計入可計算項目。

"""

    path.write_text(content, encoding="utf-8")
    return str(path)
