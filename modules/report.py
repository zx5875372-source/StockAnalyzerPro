from pathlib import Path
from datetime import datetime


def fmt(value, suffix=""):
    if value is None:
        return "資料不足"
    return f"{value}{suffix}"


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
| Piotroski F-Score | v0.3 加入 |
| 初步品質判斷 | v0.3 加入 |

---

## 三、獲利能力

| 指標 | 數值 | 判斷 |
|---|---:|---|
| ROE | {fmt(result["roe"], "%")} | {'佳' if result["roe"] is not None and result["roe"] >= 15 else '普通或資料不足'} |
| ROA | {fmt(result["roa"], "%")} | {'佳' if result["roa"] is not None and result["roa"] >= 8 else '普通或資料不足'} |

---

## 四、財務體質

| 指標 | 數值 | 判斷 |
|---|---:|---|
| 負債權益比 | {fmt(result["debt_to_equity"])} | {'安全' if result["debt_to_equity"] is not None and result["debt_to_equity"] < 80 else '需觀察'} |
| 流動比率 | {fmt(result["current_ratio"])} | {'良好' if result["current_ratio"] is not None and result["current_ratio"] >= 1.5 else '普通或資料不足'} |

---

## 五、現金流

| 指標 | 數值 | 判斷 |
|---|---:|---|
| 營業現金流 | {money(result["operating_cashflow"])} | {'正向' if result["operating_cashflow"] is not None and result["operating_cashflow"] > 0 else '需觀察'} |
| 自由現金流 | {money(result["free_cashflow"])} | {'正向' if result["free_cashflow"] is not None and result["free_cashflow"] > 0 else '需觀察'} |

---

## 六、成長性

| 項目 | 結果 |
|---|---|
| 營收成長 | v0.4 加入 |
| EPS 成長 | v0.4 加入 |
| 自由現金流成長 | v0.4 加入 |

---

## 七、估值

| 指標 | 數值 | 判斷 |
|---|---:|---|
| 本益比 PE | {fmt(result["pe"])} | {'偏低' if result["pe"] is not None and result["pe"] < 15 else '合理或偏高'} |
| 股價淨值比 PB | {fmt(result["pb"])} | {'偏低' if result["pb"] is not None and result["pb"] < 2 else '合理或偏高'} |

---

## 八、動態買點區間

| 項目 | 結果 |
|---|---|
| 合理買點 | v0.4 加入 |
| 保守買點 | v0.4 加入 |
| 積極買點 | v0.4 加入 |

---

## 九、第一目標價

| 項目 | 結果 |
|---|---|
| 第一目標價 | v0.4 加入 |
| 預估上漲空間 | v0.4 加入 |

---

## 十、風險分析

目前風險判斷：

{reasons_text}

---

## 十一、細項評分

| 項目 | 分數 |
|---|---:|
| SAP Score | {result["sap_score"]} / 100 |
| 投資等級 | {result["grade"]} |

---

## 十二、投資建議

目前版本為 SAP v0.2，已套用固定股票分析格式。

初步判斷：

- SAP Score：{result["sap_score"]} / 100
- 投資等級：{result["grade"]}
- 後續版本會加入完整 Piotroski F-Score、成長性、合理買點、第一目標價與正式投資建議。

"""

    path.write_text(content, encoding="utf-8")
    return str(path)
