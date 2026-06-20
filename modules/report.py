from pathlib import Path
from datetime import datetime


def fmt(value, suffix=""):
    if value is None:
        return "資料不足"
    return f"{value}{suffix}"


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

    piotroski = result.get("piotroski", {"score": 0, "available": 0, "items": []})
    piotroski_rows = "\n".join(
        [
            f"| {item['name']} | {yes_no(item['passed'])} | {item['note']} |"
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

---

## 二、Piotroski F-Score

| 項目 | 結果 |
|---|---:|
| 目前可計算分數 | {piotroski["score"]} / {piotroski["available"]} |
| 完整 9 項版本 | 後續版本補齊年度財報比較 |

| 細項 | 結果 | 說明 |
|---|---|---|
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

---

## 八、動態買點區間

| 項目 | 結果 |
|---|---|
| 合理買點 | 後續版本加入 |
| 保守買點 | 後續版本加入 |
| 積極買點 | 後續版本加入 |

---

## 九、第一目標價

| 項目 | 結果 |
|---|---|
| 第一目標價 | 後續版本加入 |
| 預估上漲空間 | 後續版本加入 |

---

## 十、風險分析

目前風險判斷：

{reasons_text}

---

## 十一、細項評分

| 項目 | 分數 |
|---|---:|
| Piotroski 可計算分數 | {piotroski["score"]} / {piotroski["available"]} |
| SAP Score | {result["sap_score"]} / 100 |
| 投資等級 | {result["grade"]} |

---

## 十二、投資建議

目前版本為 SAP v0.4，已加入 Financial Engine v1.0。

初步判斷：

- Piotroski 可計算分數：{piotroski["score"]} / {piotroski["available"]}
- SAP Score：{result["sap_score"]} / 100
- 投資等級：{result["grade"]}

後續版本會補齊完整年度財報比較，讓 Piotroski F-Score 9 項完整計算。

"""

    path.write_text(content, encoding="utf-8")
    return str(path)
