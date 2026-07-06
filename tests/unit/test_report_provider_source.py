import os
import tempfile
import unittest
from pathlib import Path

from modules.report import format_currency, format_percent, format_ratio, generate_markdown_report


class ReportProviderSourceTests(unittest.TestCase):
    def test_percent_formatter_formats_ratio(self):
        self.assertEqual(format_percent(0.1376), "13.76%")

    def test_percent_formatter_formats_percent_points(self):
        self.assertEqual(format_percent(1.31, value_is_ratio=False), "1.31%")

    def test_ratio_formatter_keeps_multiplier(self):
        self.assertEqual(format_ratio(1.25), "1.25")

    def test_currency_formatter_uses_grouped_two_decimals(self):
        self.assertEqual(format_currency(-3386907000), "-3,386,907,000.00")

    def test_markdown_report_includes_provider_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            try:
                os.chdir(temp_dir)
                report_path = generate_markdown_report(sample_result())
                content = Path(report_path).read_text(encoding="utf-8")
            finally:
                os.chdir(original_cwd)

        self.assertIn("| 資料來源 | FinMind |", content)
        self.assertIn("| Fallback | 否 |", content)
        self.assertIn("資料來源：FinMind", content)
        self.assertIn("Fallback：否", content)
        self.assertIn("目前版本為 StockAnalyzerPro v3.0 FinMind First Beta。", content)
        self.assertNotIn("v1.4 CLI UX Improvement", content)

    def test_report_translates_industry_and_sector(self):
        result = sample_result()
        result["industry"] = "Communication Equipment"
        result["sector"] = "Technology"

        content = render_report(result)

        self.assertIn("| 產業 | 通訊設備 |", content)
        self.assertIn("| 類別 | 科技 |", content)

    def test_report_includes_data_completeness_summary(self):
        result = sample_result()
        result["diagnostics"] = [
            "provider=finmind",
            "yahoo_enriched_fields: price, industry, sector",
            "still_missing_fields: -",
        ]

        content = render_report(result)

        self.assertIn("## 資料完整度摘要", content)
        self.assertIn("| 資料完整度 | 完整 |", content)
        self.assertIn("| 主要資料來源 | FinMind |", content)
        self.assertIn("| 補充資料來源 | Yahoo Finance |", content)
        self.assertIn("| 目前缺漏欄位 | 無 |", content)

    def test_report_marks_critical_missing_fields_as_insufficient(self):
        result = sample_result()
        result["price"] = None
        result["diagnostics"] = ["still_missing_fields: current.eps, current.revenue"]

        content = render_report(result)

        self.assertIn("| 資料完整度 | 資料不足 |", content)
        self.assertIn("| 目前缺漏欄位 | current.eps, current.revenue, current_price |", content)

    def test_d_grade_plain_language_judgement(self):
        result = sample_result()
        result["grade"] = "D級"
        result["sap_score"] = 24
        result["free_cashflow"] = -100
        result["operating_cashflow"] = -50
        result["pe_judgement"] = "偏高"
        result["pb_judgement"] = "偏高"
        result["price"] = 120
        result["valuation"]["first_target_price"] = 100
        result["valuation"]["upside_percent"] = -16.67

        content = render_report(result)

        self.assertIn("### 白話判斷", content)
        self.assertIn("目前不建議買進。", content)
        self.assertIn("SAP 評分偏低", content)
        self.assertIn("自由現金流為負", content)
        self.assertIn("PE / PB 偏高", content)

    def test_price_above_first_target_warning(self):
        result = sample_result()
        result["price"] = 120
        result["valuation"]["first_target_price"] = 100
        result["valuation"]["upside_percent"] = -16.67

        content = render_report(result)

        self.assertIn("⚠ 目前股價已高於第一目標價，追價風險偏高。", content)
        self.assertIn("預估上漲空間為負，代表目前價格高於模型估算目標價。", content)

    def test_valuation_numbers_are_formatted_to_two_decimals(self):
        result = sample_result()
        result["price"] = 123.456
        result["pe"] = 12.3456
        result["pb"] = 1.2345
        result["valuation"]["book_value_per_share"] = 56.789
        result["valuation"]["reasonable_buy"] = 90.123
        result["valuation"]["first_target_price"] = 120.987

        content = render_report(result)

        self.assertIn("| 目前股價 | 123.46 |", content)
        self.assertIn("| 本益比 PE | 12.35 |", content)
        self.assertIn("| 股價淨值比 PB | 1.23 |", content)
        self.assertIn("| 每股淨值 | 56.79 |", content)
        self.assertIn("| 合理買點 | 90.12 |", content)
        self.assertIn("| 第一目標價 | 120.99 |", content)

    def test_report_includes_valuation_profile(self):
        result = sample_result()
        result["valuation"].update(
            {
                "valuation_profile": "通訊設備",
                "valuation_source": "industry_profile_v2",
                "industry_mapping": {"industry": "Communication Equipment", "profile": "通訊設備"},
                "pe_range": (15, 25),
                "pb_range": (1.5, 3.5),
                "reasonable_pe": 20,
                "reasonable_pb": 2.5,
            }
        )

        content = render_report(result)

        self.assertIn("### 估值模型", content)
        self.assertIn("| 產業估值 | 通訊設備 |", content)
        self.assertIn("| PE 區間 | 15~25 |", content)
        self.assertIn("| PB 區間 | 1.5~3.5 |", content)
        self.assertIn("| 本次採用 PE | 20 |", content)
        self.assertIn("| 本次採用 PB | 2.5 |", content)
        self.assertIn("| 合理 PE | 20.00 | 動態產業估值 |", content)
        self.assertIn("| 合理 PB | 2.50 | 動態產業估值 |", content)

    def test_report_renders_technical_analysis(self):
        result = sample_result()
        result["technical"] = sample_technical()

        content = render_report(result)

        self.assertIn("## 技術分析", content)
        self.assertIn("| MA20 | 100.00 |", content)
        self.assertIn("| MA60 | 95.00 |", content)
        self.assertIn("| RSI14 | 55.00 |", content)
        self.assertIn("| RSI 狀態 | 正常 |", content)
        self.assertIn("| MACD | 1.20 |", content)
        self.assertIn("| Signal | 0.80 |", content)
        self.assertIn("| Histogram | 0.40 |", content)
        self.assertIn("| MACD 狀態 | 偏多 |", content)
        self.assertIn("| 成交量倍率 | 1.50 |", content)
        self.assertIn("| Trend Score | 80.00 |", content)
        self.assertIn("| 技術評級 | A |", content)
        self.assertIn("technical_source: Yahoo Finance", content)

    def test_report_renders_total_score(self):
        result = sample_result()
        result["technical"] = sample_technical()

        content = render_report(result)

        self.assertIn("## 綜合分析", content)
        self.assertIn("| SAP Score | 90.00 |", content)
        self.assertIn("| Trend Score | 80.00 |", content)
        self.assertIn("| Total Score | 86.00 |", content)
        self.assertIn("不影響 SAP Score 或原本投資等級", content)

    def test_unmapped_raw_fields_are_advanced_diagnostics_only(self):
        result = sample_result()
        result["diagnostics"] = [
            "缺少欄位：current.long_term_debt_missing",
            "unmapped_raw_fields: CashAndCashEquivalents (+70 more)",
        ]

        content = render_report(result)
        general_section = content.split("### 一般診斷", 1)[1].split("### 進階診斷", 1)[0]
        advanced_section = content.split("### 進階診斷", 1)[1].split("---", 1)[0]

        self.assertNotIn("unmapped_raw_fields", general_section)
        self.assertIn("unmapped_raw_fields: CashAndCashEquivalents (+70 more)", advanced_section)

    def test_piotroski_header_uses_comparison_value(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn("| 細項 | 結果 | 目前值 | 比較值 | 說明 |", content)
        self.assertNotIn("去年值/比較值", content)

    def test_positive_roa_comparison_value_is_not_applicable(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn("| 1. ROA 為正 | 通過 | 1.31% | 不適用 | current ROA > 0 加 1 分 |", content)
        self.assertNotIn("| 1. ROA 為正 | 通過 | 1.31% | 資料不足 |", content)

    def test_positive_operating_cashflow_comparison_value_is_not_applicable(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn(
            "| 2. 營業現金流為正 | 未通過 | -3,386,907,000.00 | 不適用 | "
            "current operating_cashflow > 0 加 1 分 |",
            content,
        )
        self.assertNotIn("| 2. 營業現金流為正 | 未通過 | -3,386,907,000.00 | 資料不足 |", content)

    def test_cashflow_greater_than_net_income_shows_current_net_income_as_comparison(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn(
            "| 4. 營業現金流大於淨利 | 未通過 | -3,386,907,000.00 | 1,132,064,000.00 | "
            "current operating_cashflow > current net_income 加 1 分 |",
            content,
        )

    def test_piotroski_period_comparison_items_still_show_previous_values(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn("| 3. ROA 較去年提升 | 未通過 | 1.31% | 1.11% |", content)
        self.assertIn("| 5. 長期負債比下降 | 未通過 | 42.00% | 35.00% |", content)
        self.assertIn("| 6. 流動比率提升 | 通過 | 1.25 | 1.10 |", content)
        self.assertIn("| 7. 股本未稀釋 | 通過 | 100,000.00 | 100,000.00 |", content)
        self.assertIn("| 8. 毛利率提升 | 通過 | 30.00% | 25.00% |", content)
        self.assertIn("| 9. 資產週轉率提升 | 未通過 | 0.80 | 0.90 |", content)

    def test_piotroski_roa_displays_percent(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn("| 1. ROA 為正 | 通過 | 1.31% | 不適用 |", content)
        self.assertIn("| 3. ROA 較去年提升 | 未通過 | 1.31% | 1.11% |", content)

    def test_piotroski_gross_margin_displays_percent(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn("| 8. 毛利率提升 | 通過 | 30.00% | 25.00% |", content)

    def test_piotroski_long_term_debt_ratio_displays_percent(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn("| 5. 長期負債比下降 | 未通過 | 42.00% | 35.00% |", content)

    def test_piotroski_current_ratio_remains_multiplier(self):
        result = sample_result()
        result["piotroski"]["items"] = piotroski_items()

        content = render_report(result)

        self.assertIn("| 6. 流動比率提升 | 通過 | 1.25 | 1.10 |", content)
        self.assertNotIn("| 6. 流動比率提升 | 通過 | 125.00% | 110.00% |", content)


def sample_result():
    return {
        "symbol": "2330.TW",
        "company_name": "台積電",
        "industry": "半導體",
        "sector": "科技",
        "price": 1000,
        "current_period": "2025-12-31",
        "previous_period": "2024-12-31",
        "provider_source": "FinMind",
        "provider_fallback_used": False,
        "provider_fallback_reason": "",
        "pe": 20,
        "pb": 5,
        "roe": 20,
        "roa": 10,
        "debt_to_equity": 50,
        "current_ratio": 2,
        "free_cashflow": 100,
        "operating_cashflow": 200,
        "diagnostics": [],
        "roe_judgement": "佳",
        "roa_judgement": "佳",
        "debt_to_equity_judgement": "安全",
        "current_ratio_judgement": "良好",
        "operating_cashflow_judgement": "正向",
        "free_cashflow_judgement": "正向",
        "pe_judgement": "合理",
        "pb_judgement": "偏高",
        "sap_score": 90,
        "grade": "A",
        "reasons": ["測試"],
        "piotroski": {"score": 9, "available": 9, "total": 9, "items": []},
        "valuation": {
            "eps": 5,
            "book_value_per_share": 20,
            "reasonable_pe": 20,
            "reasonable_pb": 3,
            "pe_fair_price": 100,
            "pb_fair_price": 60,
            "fair_price": 80,
            "conservative_buy": 60,
            "reasonable_buy": 68,
            "aggressive_buy": 76,
            "first_target_price": 92,
            "upside_percent": -8,
        },
        "growth": {"score": 0, "max": 13, "items": []},
        "scoring": {"categories": {}},
    }


def render_report(result):
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            report_path = generate_markdown_report(result)
            return Path(report_path).read_text(encoding="utf-8")
        finally:
            os.chdir(original_cwd)


def piotroski_items():
    return [
        {
            "name": "1. ROA 為正",
            "passed": True,
            "current_value": 1.31,
            "previous_value": None,
            "note": "current ROA > 0 加 1 分",
        },
        {
            "name": "2. 營業現金流為正",
            "passed": False,
            "current_value": -3386907000,
            "previous_value": None,
            "note": "current operating_cashflow > 0 加 1 分",
        },
        {
            "name": "3. ROA 較去年提升",
            "passed": False,
            "current_value": 1.31,
            "previous_value": 1.11,
            "note": "current ROA > previous ROA 加 1 分",
        },
        {
            "name": "4. 營業現金流大於淨利",
            "passed": False,
            "current_value": -3386907000,
            "previous_value": 1132064000,
            "note": "current operating_cashflow > current net_income 加 1 分",
        },
        {
            "name": "5. 長期負債比下降",
            "passed": False,
            "current_value": 0.42,
            "previous_value": 0.35,
            "note": "current long_term_debt / total_assets < previous long_term_debt / total_assets 加 1 分",
        },
        {
            "name": "6. 流動比率提升",
            "passed": True,
            "current_value": 1.25,
            "previous_value": 1.10,
            "note": "current current_ratio > previous current_ratio 加 1 分",
        },
        {
            "name": "7. 股本未稀釋",
            "passed": True,
            "current_value": 100000,
            "previous_value": 100000,
            "note": "current shares_outstanding <= previous shares_outstanding 加 1 分",
        },
        {
            "name": "8. 毛利率提升",
            "passed": True,
            "current_value": 0.30,
            "previous_value": 0.25,
            "note": "current gross_profit / revenue > previous gross_profit / revenue 加 1 分",
        },
        {
            "name": "9. 資產週轉率提升",
            "passed": False,
            "current_value": 0.80,
            "previous_value": 0.90,
            "note": "current revenue / total_assets > previous revenue / total_assets 加 1 分",
        },
    ]


def sample_technical():
    return {
        "trend_score": 80,
        "technical_grade": "A",
        "ma20": 100,
        "ma60": 95,
        "ma120": 90,
        "ma240": 85,
        "rsi14": 55,
        "rsi_status": "正常",
        "macd": 1.2,
        "macd_signal": 0.8,
        "macd_histogram": 0.4,
        "macd_status": "偏多",
        "volume_ratio": 1.5,
        "golden_cross": True,
        "death_cross": False,
        "diagnostics": [
            "technical_source: Yahoo Finance",
            "technical_period: 2y",
            "technical_price_count: 260",
            "technical_missing_fields: -",
        ],
    }


if __name__ == "__main__":
    unittest.main()
