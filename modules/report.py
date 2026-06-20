from pathlib import Path
from datetime import datetime


def fmt(value):
    if value is None:
        return "資料不足"
    return value


def money(value):
    if value is None:
        return "資料不足"
    return f"{value:,}"


def generate_markdown_report(result: dict) -> str:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    symbol = result["symbol"]
    today = datetime.now().strftime("%Y%m%d")
    path = reports_dir / f"{symbol}_{today}.md"

    reasons_text = "\n".join([f"- {r}" for r in result["reasons"]])

    content = f"""# {symbol} 股票分析報告

## 一、基本資料

| 項目 | 內容 |
|---|---|
| 公司名稱 | {result["company_name"]} |
| 產業 | {result["industry"]} |
| 類別 | {result["sector"]} |
| 目前股價 | {fmt(result["price"])} |

---

## 二、SAP Score

| 項目 | 結果 |
|---|---:|
| SAP Score | {result["sap_score"]} / 100 |
| 投資等級 | {result["grade"]} |

---

## 三、獲利能力

| 指標 | 數值 |
|---|---:|
| ROE | {fmt(result["roe"])}% |
| ROA | {fmt(result["roa"])}% |

---

## 四、財務體質

| 指標 | 數值 |
|---|---:|
| 負債權益比 | {fmt(result["debt_to_equity"])} |
| 流動比率 | {fmt(result["current_ratio"])} |

---

## 五、現金流

| 指標 | 數值 |
|---|---:|
| 營業現金流 | {money(result["operating_cashflow"])} |
| 自由現金流 | {money(result["free_cashflow"])} |

---

## 六、估值

| 指標 | 數值 |
|---|---:|
| 本益比 PE | {fmt(result["pe"])} |
| 股價淨值比 PB | {fmt(result["pb"])} |

---

## 七、加分與扣分原因

{reasons_text}

---

## 八、初步投資建議

此版本為 SAP v0.1 初版分析，主要依據 yfinance 可取得資料進行初步評分。

後續版本會加入：

- Piotroski F-Score
- 成長性
- 合理買點
- 第一目標價
- 風險評估
- 固定格式完整投資建議
"""

    path.write_text(content, encoding="utf-8")
    return str(path)
