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

SECTION_SEPARATOR = "\n\n---\n\n"


def generate_markdown_report(result: dict) -> str:
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    symbol = result["symbol"]
    today = datetime.now().strftime("%Y%m%d")
    path = reports_dir / f"{symbol}_{today}.md"

    path.write_text(render_report_content(result), encoding="utf-8")
    return str(path)


def render_report_content(result: dict) -> str:
    piotroski = result.get("piotroski", {"score": 0, "available": 0, "items": []})
    valuation = result.get("valuation", {})
    growth = result.get("growth", {"score": 0, "max": 13, "items": []})
    technical = technical_result(result)

    sections = [
        render_basic_info_section(result),
        render_completeness_section(result),
        render_piotroski_section(piotroski),
        render_profitability_section(result),
        render_financial_health_section(result),
        render_cashflow_section(result),
        render_growth_section(growth),
        render_valuation_section(result, valuation),
        render_technical_section(technical),
        render_combined_score_section(result, technical),
        render_industry_ranking_section(result),
        render_buy_zone_section(valuation),
        render_target_price_section(valuation),
        render_risk_section(result),
        render_diagnostics_section(result),
        render_detailed_scores_section(result, piotroski),
        render_advice_section(result, piotroski, valuation, growth),
    ]
    return SECTION_SEPARATOR.join(sections) + "\n\n"


def render_basic_info_section(result: dict) -> str:
    fallback_text = "是" if result.get("provider_fallback_used") else "否"
    fallback_reason = result.get("provider_fallback_reason") or "-"
    provider_source = result.get("provider_source", "未知")
    return "\n".join(
        [
            f"# {result['symbol']} 固定格式股票分析報告",
            "",
            "## 一、公司基本資料",
            "",
            "| 項目 | 內容 |",
            "|---|---|",
            f"| 股票代號 | {result['symbol']} |",
            f"| 公司名稱 | {result['company_name']} |",
            f"| 產業 | {translate_industry(result['industry'])} |",
            f"| 類別 | {translate_industry(result['sector'])} |",
            f"| 目前股價 | {fmt(result['price'])} |",
            f"| 最新財報期 | {fmt(result['current_period'])} |",
            f"| 前一財報期 | {fmt(result['previous_period'])} |",
            f"| 資料來源 | {provider_source} |",
            f"| Fallback | {fallback_text} |",
            f"| Fallback 原因 | {fallback_reason} |",
            "",
            f"資料來源：{provider_source}",
            "",
            f"Fallback：{fallback_text}",
        ]
    )


def render_completeness_section(result: dict) -> str:
    completeness = data_completeness_summary(result)
    return "\n".join(
        [
            "## 資料完整度摘要",
            "",
            "| 項目 | 結果 |",
            "|---|---|",
            f"| 資料完整度 | {completeness['status']} |",
            f"| 主要資料來源 | {completeness['primary_source']} |",
            f"| 補充資料來源 | {completeness['supplement_source']} |",
            f"| 目前缺漏欄位 | {completeness['missing_text']} |",
        ]
    )


def render_piotroski_section(piotroski: dict) -> str:
    piotroski_total = piotroski.get("total", 9)
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
    return "\n".join(
        [
            "## 二、Piotroski F-Score",
            "",
            "| 項目 | 結果 |",
            "|---|---:|",
            f"| 完整分數 | {piotroski['score']} / {piotroski_total} |",
            f"| 可計算項目 | {piotroski['score']} / {piotroski['available']} |",
            "",
            "| 細項 | 結果 | 目前值 | 比較值 | 說明 |",
            "|---|---|---:|---:|---|",
            piotroski_rows,
        ]
    )


def render_profitability_section(result: dict) -> str:
    return "\n".join(
        [
            "## 三、獲利能力",
            "",
            "| 指標 | 數值 | 判斷 |",
            "|---|---:|---|",
            f"| ROE | {fmt(result['roe'], '%')} | {result['roe_judgement']} |",
            f"| ROA | {fmt(result['roa'], '%')} | {result['roa_judgement']} |",
        ]
    )


def render_financial_health_section(result: dict) -> str:
    return "\n".join(
        [
            "## 四、財務體質",
            "",
            "| 指標 | 數值 | 判斷 |",
            "|---|---:|---|",
            f"| 負債權益比 | {fmt(result['debt_to_equity'], '%')} | {result['debt_to_equity_judgement']} |",
            f"| 流動比率 | {fmt(result['current_ratio'])} | {result['current_ratio_judgement']} |",
        ]
    )


def render_cashflow_section(result: dict) -> str:
    return "\n".join(
        [
            "## 五、現金流",
            "",
            "| 指標 | 數值 | 判斷 |",
            "|---|---:|---|",
            f"| 營業現金流 | {money(result['operating_cashflow'])} | {result['operating_cashflow_judgement']} |",
            f"| 自由現金流 | {money(result['free_cashflow'])} | {result['free_cashflow_judgement']} |",
        ]
    )


def render_growth_section(growth: dict) -> str:
    return "\n".join(
        [
            "## 六、成長性",
            "",
            "| 項目 | 成長率 | 分數 | 判斷 |",
            "|---|---:|---:|---|",
            f'| 營收成長 | {percent(growth["items"][0]["growth_rate"]) if len(growth["items"]) > 0 else "資料不足"} | {growth["items"][0]["score"] if len(growth["items"]) > 0 else 0} / {growth["items"][0]["max"] if len(growth["items"]) > 0 else 5} | {growth["items"][0]["note"] if len(growth["items"]) > 0 else "資料不足"} |',
            f'| EPS 成長 | {percent(growth["items"][1]["growth_rate"]) if len(growth["items"]) > 1 else "資料不足"} | {growth["items"][1]["score"] if len(growth["items"]) > 1 else 0} / {growth["items"][1]["max"] if len(growth["items"]) > 1 else 5} | {growth["items"][1]["note"] if len(growth["items"]) > 1 else "資料不足"} |',
            f'| 自由現金流成長 | {percent(growth["items"][2]["growth_rate"]) if len(growth["items"]) > 2 else "資料不足"} | {growth["items"][2]["score"] if len(growth["items"]) > 2 else 0} / {growth["items"][2]["max"] if len(growth["items"]) > 2 else 3} | {growth["items"][2]["note"] if len(growth["items"]) > 2 else "資料不足"} |',
        ]
    )


def render_valuation_section(result: dict, valuation: dict) -> str:
    valuation_model = valuation_model_text(valuation)
    return "\n".join(
        [
            "## 七、估值",
            "",
            "### 估值模型",
            "",
            "| 項目 | 結果 |",
            "|---|---|",
            f"| 產業估值 | {valuation_model['profile']} |",
            f"| PE 區間 | {valuation_model['pe_range']} |",
            f"| PB 區間 | {valuation_model['pb_range']} |",
            f"| 本次採用 PE | {valuation_model['reasonable_pe']} |",
            f"| 本次採用 PB | {valuation_model['reasonable_pb']} |",
            "",
            "| 指標 | 數值 | 判斷 |",
            "|---|---:|---|",
            f"| 本益比 PE | {fmt(result['pe'])} | {result['pe_judgement']} |",
            f"| 股價淨值比 PB | {fmt(result['pb'])} | {result['pb_judgement']} |",
            f"| EPS | {metric(valuation.get('eps'))} | 估值輸入 |",
            f"| 每股淨值 | {metric(valuation.get('book_value_per_share'))} | 估值輸入 |",
            f"| 合理 PE | {metric(valuation.get('reasonable_pe'))} | 動態產業估值 |",
            f"| 合理 PB | {metric(valuation.get('reasonable_pb'))} | 動態產業估值 |",
            f"| PE 合理價 | {metric(valuation.get('pe_fair_price'))} | EPS × 合理 PE |",
            f"| PB 合理價 | {metric(valuation.get('pb_fair_price'))} | 每股淨值 × 合理 PB |",
            f"| 綜合合理價 | {metric(valuation.get('fair_price'))} | PE/PB 合理價平均 |",
            "",
            "### 估值警示",
            "",
            valuation_warnings(result),
        ]
    )


def render_technical_section(technical: dict) -> str:
    return "\n".join(
        [
            "## 技術分析",
            "",
            "| 指標 | 數值 |",
            "|---|---:|",
            f"| MA20 | {metric(technical.get('ma20'))} |",
            f"| MA60 | {metric(technical.get('ma60'))} |",
            f"| MA120 | {metric(technical.get('ma120'))} |",
            f"| MA240 | {metric(technical.get('ma240'))} |",
            f"| RSI14 | {metric(technical.get('rsi14'))} |",
            f"| RSI 狀態 | {technical.get('rsi_status')} |",
            f"| MACD | {metric(technical.get('macd'))} |",
            f"| Signal | {metric(technical.get('macd_signal'))} |",
            f"| Histogram | {metric(technical.get('macd_histogram'))} |",
            f"| MACD 狀態 | {technical.get('macd_status')} |",
            f"| 黃金交叉 | {yes_no_plain(technical.get('golden_cross', False))} |",
            f"| 死亡交叉 | {yes_no_plain(technical.get('death_cross', False))} |",
            f"| 成交量倍率 | {format_ratio(technical.get('volume_ratio'))} |",
            f"| 技術評分 | {metric(technical.get('trend_score'))} |",
            f"| 技術等級 | {technical.get('technical_grade')} |",
            "",
            "### 技術診斷",
            "",
            diagnostic_lines(technical.get("diagnostics", [])),
        ]
    )


def render_combined_score_section(result: dict, technical: dict) -> str:
    combined_total_score = total_score(result.get("sap_score"), technical.get("trend_score"))
    return "\n".join(
        [
            "## 綜合分析",
            "",
            "| 指標 | 分數 |",
            "|---|---:|",
            f"| SAP 基本面評分 | {metric(result.get('sap_score'))} |",
            f"| 技術評分 | {metric(technical.get('trend_score'))} |",
            f"| 綜合評分 | {metric(combined_total_score)} |",
            "",
            "綜合評分 = SAP 基本面評分 * 0.6 + 技術評分 * 0.4。此分數只供參考，不影響 SAP Score 或原本投資等級。",
        ]
    )


def render_industry_ranking_section(result: dict) -> str:
    industry_ranking = industry_ranking_result(result)
    return "\n".join(
        [
            "## 產業排名",
            "",
            "| 項目 | 結果 |",
            "|---|---|",
            f"| 所屬產業 | {industry_ranking['industry_name']} |",
            f"| 產業股票數 | {industry_ranking['industry_size']} |",
            f"| SAP 排名 | {industry_ranking['sap_rank']} |",
            f"| 技術排名 | {industry_ranking['trend_rank']} |",
            f"| 綜合排名 | {industry_ranking['total_rank']} |",
            f"| 百分位 | {industry_ranking['top_percent']} |",
            f"| 評價 | {industry_ranking['rating']} |",
            "",
            industry_ranking["summary_text"],
        ]
    )


def render_buy_zone_section(valuation: dict) -> str:
    return "\n".join(
        [
            "## 八、動態買點區間",
            "",
            "| 項目 | 結果 |",
            "|---|---|",
            f"| 保守買點 | {metric(valuation.get('conservative_buy'))} |",
            f"| 合理買點 | {metric(valuation.get('reasonable_buy'))} |",
            f"| 積極買點 | {metric(valuation.get('aggressive_buy'))} |",
        ]
    )


def render_target_price_section(valuation: dict) -> str:
    return "\n".join(
        [
            "## 九、第一目標價",
            "",
            "| 項目 | 結果 |",
            "|---|---|",
            f"| 第一目標價 | {metric(valuation.get('first_target_price'))} |",
            f"| 預估上漲空間 | {fmt(valuation.get('upside_percent'), '%')} |",
        ]
    )


def render_risk_section(result: dict) -> str:
    reasons_text = "\n".join([f"- {r}" for r in result["reasons"]])
    return "\n".join(
        [
            "## 十、風險分析",
            "",
            "目前風險判斷：",
            "",
            reasons_text,
        ]
    )


def render_diagnostics_section(result: dict) -> str:
    diagnostics = result.get("diagnostics") or ["無明顯缺漏"]
    general_diagnostics, advanced_diagnostics = split_diagnostics(diagnostics)
    return "\n".join(
        [
            "## 十一、資料完整度與診斷",
            "",
            "### 一般診斷",
            "",
            diagnostic_lines(general_diagnostics),
            "",
            "### 進階診斷",
            "",
            diagnostic_lines(advanced_diagnostics),
        ]
    )


def render_detailed_scores_section(result: dict, piotroski: dict) -> str:
    piotroski_total = piotroski.get("total", 9)
    scoring = result.get("scoring", {"categories": {}})
    scoring_categories = default_scoring_categories()
    scoring_categories.update(scoring.get("categories", {}))
    category_rows = [
        ("Piotroski F-Score", "piotroski"),
        ("獲利能力", "profitability"),
        ("財務體質", "financial_health"),
        ("現金流", "cashflow"),
        ("估值", "valuation"),
        ("成長性", "growth"),
    ]
    return "\n".join(
        [
            "## 十二、細項評分",
            "",
            "| 項目 | 分數 |",
            "|---|---:|",
            f"| Piotroski 完整分數 | {piotroski['score']} / {piotroski_total} |",
            f"| Piotroski 可計算項目 | {piotroski['score']} / {piotroski['available']} |",
            f"| SAP Score | {result['sap_score']} / 100 |",
            f"| 投資等級 | {result['grade']} |",
            "",
            "| 大類 | 分數 |",
            "|---|---:|",
            *[
                f"| {label} | {scoring_categories[key]['score']} / {scoring_categories[key]['max']} |"
                for label, key in category_rows
            ],
            "",
            "| 大類 | 項目 | 分數 | 加分原因 |",
            "|---|---|---:|---|",
            scoring_item_rows(scoring_categories),
        ]
    )


def render_advice_section(result: dict, piotroski: dict, valuation: dict, growth: dict) -> str:
    piotroski_total = piotroski.get("total", 9)
    plain_judgement = plain_language_judgement(result)
    return "\n".join(
        [
            "## 十三、投資建議",
            "",
            "目前版本為 StockAnalyzerPro v3.0 FinMind First Beta。",
            "",
            "### 白話判斷",
            "",
            plain_judgement["summary"],
            "",
            "原因：",
            "",
            numbered_lines(plain_judgement["reasons"]),
            "",
            "### 評分摘要",
            "",
            "初步判斷：",
            "",
            f"- Piotroski 完整分數：{piotroski['score']} / {piotroski_total}",
            f"- Piotroski 可計算項目：{piotroski['score']} / {piotroski['available']}",
            f"- SAP Score：{result['sap_score']} / 100",
            f"- 投資等級：{result['grade']}",
            f"- 成長性分數：{growth.get('score', 0)} / {growth.get('max', 13)}",
            f"- 綜合合理價：{metric(valuation.get('fair_price'))}",
            f"- 第一目標價：{metric(valuation.get('first_target_price'))}",
            "",
            "Piotroski 明細使用 current / previous 財報資料計算；資料不足的項目不計入可計算項目。",
        ]
    )
