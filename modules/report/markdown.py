from datetime import datetime
from pathlib import Path

from modules.report.diagnostics import (
    data_completeness_summary,
    diagnostic_lines,
    split_diagnostics,
)
from modules.report.formatters import (
    fmt,
    format_ratio,
    metric,
    money,
    numbered_lines,
    percent,
    translate_industry,
    yes_no,
    yes_no_plain,
)
from modules.report.sections import (
    default_scoring_categories,
    industry_ranking_result,
    piotroski_comparison_value,
    piotroski_value,
    plain_language_judgement,
    scoring_item_rows,
    technical_result,
    total_score,
    valuation_model_text,
    valuation_warnings,
)


def generate_markdown_report(result: dict) -> str:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    symbol = result["symbol"]
    today = datetime.now().strftime("%Y%m%d")
    path = reports_dir / f"{symbol}_{today}.md"

    reasons_text = "\n".join([f"- {r}" for r in result["reasons"]])
    diagnostics = result.get("diagnostics") or ["無明顯缺漏"]
    general_diagnostics, advanced_diagnostics = split_diagnostics(diagnostics)
    general_diagnostics_text = diagnostic_lines(general_diagnostics)
    advanced_diagnostics_text = diagnostic_lines(advanced_diagnostics)

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
    valuation_model = valuation_model_text(valuation)
    technical = technical_result(result)
    combined_total_score = total_score(result.get("sap_score"), technical.get("trend_score"))
    technical_diagnostics_text = diagnostic_lines(technical.get("diagnostics", []))
    industry_ranking = industry_ranking_result(result)
    piotroski_rows = "\n".join(
        [
            "| "
            f"{item['name']} | "
            f"{yes_no(item['passed'])} | "
            f"{piotroski_value(item, 'current_value')} | "
            f"{piotroski_comparison_value(item)} | "
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

| 細項 | 結果 | 目前值 | 比較值 | 說明 |
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

### 估值模型

| 項目 | 結果 |
|---|---|
| 產業估值 | {valuation_model["profile"]} |
| PE 區間 | {valuation_model["pe_range"]} |
| PB 區間 | {valuation_model["pb_range"]} |
| 本次採用 PE | {valuation_model["reasonable_pe"]} |
| 本次採用 PB | {valuation_model["reasonable_pb"]} |

| 指標 | 數值 | 判斷 |
|---|---:|---|
| 本益比 PE | {fmt(result["pe"])} | {result["pe_judgement"]} |
| 股價淨值比 PB | {fmt(result["pb"])} | {result["pb_judgement"]} |
| EPS | {metric(valuation.get("eps"))} | 估值輸入 |
| 每股淨值 | {metric(valuation.get("book_value_per_share"))} | 估值輸入 |
| 合理 PE | {metric(valuation.get("reasonable_pe"))} | 動態產業估值 |
| 合理 PB | {metric(valuation.get("reasonable_pb"))} | 動態產業估值 |
| PE 合理價 | {metric(valuation.get("pe_fair_price"))} | EPS × 合理 PE |
| PB 合理價 | {metric(valuation.get("pb_fair_price"))} | 每股淨值 × 合理 PB |
| 綜合合理價 | {metric(valuation.get("fair_price"))} | PE/PB 合理價平均 |

### 估值警示

{valuation_warning_text}

---

## 技術分析

| 指標 | 數值 |
|---|---:|
| MA20 | {metric(technical.get("ma20"))} |
| MA60 | {metric(technical.get("ma60"))} |
| MA120 | {metric(technical.get("ma120"))} |
| MA240 | {metric(technical.get("ma240"))} |
| RSI14 | {metric(technical.get("rsi14"))} |
| RSI 狀態 | {technical.get("rsi_status")} |
| MACD | {metric(technical.get("macd"))} |
| Signal | {metric(technical.get("macd_signal"))} |
| Histogram | {metric(technical.get("macd_histogram"))} |
| MACD 狀態 | {technical.get("macd_status")} |
| 黃金交叉 | {yes_no_plain(technical.get("golden_cross", False))} |
| 死亡交叉 | {yes_no_plain(technical.get("death_cross", False))} |
| 成交量倍率 | {format_ratio(technical.get("volume_ratio"))} |
| 技術評分 | {metric(technical.get("trend_score"))} |
| 技術等級 | {technical.get("technical_grade")} |

### 技術診斷

{technical_diagnostics_text}

---

## 綜合分析

| 指標 | 分數 |
|---|---:|
| SAP 基本面評分 | {metric(result.get("sap_score"))} |
| 技術評分 | {metric(technical.get("trend_score"))} |
| 綜合評分 | {metric(combined_total_score)} |

綜合評分 = SAP 基本面評分 * 0.6 + 技術評分 * 0.4。此分數只供參考，不影響 SAP Score 或原本投資等級。

---

## 產業排名

| 項目 | 結果 |
|---|---|
| 所屬產業 | {industry_ranking["industry_name"]} |
| 產業股票數 | {industry_ranking["industry_size"]} |
| SAP 排名 | {industry_ranking["sap_rank"]} |
| 技術排名 | {industry_ranking["trend_rank"]} |
| 綜合排名 | {industry_ranking["total_rank"]} |
| 百分位 | {industry_ranking["top_percent"]} |
| 評價 | {industry_ranking["rating"]} |

{industry_ranking["summary_text"]}

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
