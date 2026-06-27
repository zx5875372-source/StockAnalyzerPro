import tempfile
import unittest
from pathlib import Path

from models.financial_data import FinancialData
from scan import (
    display_stock_name,
    recommendation_for_grade,
    resolve_stock_name,
    write_summary,
    write_top10,
    write_watchlist_report,
)


class ScanReportTests(unittest.TestCase):
    def test_top10_markdown_table_columns_are_consistent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "top10.md"
            write_top10(sample_rows(), output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assert_markdown_tables_consistent(content)
        self.assertIn("| 排名 | 股票代號 | 股票名稱 | SAP評分 | 等級 | Piotroski | 合理買點 | 第一目標價 | 建議 | 資料來源 |", content)
        self.assertEqual(markdown_column_count("| 排名 | 股票代號 | 股票名稱 | SAP評分 | 等級 | Piotroski | 合理買點 | 第一目標價 | 建議 | 資料來源 |"), 10)
        self.assertIn("| 1 | 2330.TW | 台積電 | 95 | A | 9/9 | 512.35 | 620.99 | 優先研究 | FinMind |", content)
        self.assertIn("| 2 | 2454.TW | 聯發科 | 70 | B | 7/9 | - | - | 可觀察 | Yahoo Finance（FinMind fallback） |", content)

    def test_watchlist_report_table_columns_are_consistent(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "watchlist_report.md"
            write_watchlist_report(sample_rows(), output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assert_markdown_tables_consistent(content)
        self.assertIn("StockAnalyzerPro v3.0", content)
        self.assertNotIn("Taiwan Semiconductor Manufacturing Company Limited", content)
        self.assertNotIn("Longwell Company", content)
        self.assertNotIn("v1.4 CLI UX Improvement", content)

    def test_scan_summary_tables_are_consistent_and_version_is_updated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "scan_summary.md"
            write_summary(sample_rows(), output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assert_markdown_tables_consistent(content)
        self.assertIn("股票分析系統", content)
        self.assertIn("| 1 | 2454.TW | 聯發科 | 2 | 90 | current.revenue, previous.net_income |", content)
        self.assertNotIn("v1.4 CLI UX Improvement", content)

    def test_stock_name_prefers_chinese_fallback_before_yfinance_name(self):
        data = FinancialData(symbol="2330.TW", company_name="Taiwan Semiconductor Manufacturing Company Limited")

        name = resolve_stock_name({"symbol": "2330", "name": "台積電"}, data)

        self.assertEqual(name, "台積電")

    def test_stock_name_fallback_map_handles_common_taiwan_symbols(self):
        data = FinancialData(symbol="6290.TWO", company_name="未知公司")

        name = resolve_stock_name({"symbol": "6290.TWO", "name": ""}, data)

        self.assertEqual(name, "良維")

    def test_stock_name_fallback_map_handles_6285(self):
        data = FinancialData(symbol="6285.TW", company_name="Unknown Company")

        name = resolve_stock_name({"symbol": "6285.TW", "name": ""}, data)

        self.assertEqual(name, "啟碁")

    def test_display_stock_name_prefers_chinese_fallback_over_english_row_name(self):
        self.assertEqual(
            display_stock_name({"symbol": "6290.TWO", "name": "Longwell Company"}),
            "良維",
        )

    def test_long_english_name_is_truncated_when_no_fallback_exists(self):
        data = FinancialData(symbol="9999.TW", company_name="Very Long English Corporation Name")

        name = resolve_stock_name({"symbol": "9999.TW", "name": ""}, data)

        self.assertEqual(name, "Very Long Englis...")

    def test_recommendation_by_grade(self):
        self.assertEqual(recommendation_for_grade("S級"), "優先研究")
        self.assertEqual(recommendation_for_grade("A"), "優先研究")
        self.assertEqual(recommendation_for_grade("B"), "可觀察")
        self.assertEqual(recommendation_for_grade("C"), "保守觀察")
        self.assertEqual(recommendation_for_grade("D"), "暫不建議")

    def assert_markdown_tables_consistent(self, content: str):
        current_width = None
        for line in content.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                current_width = None
                continue
            width = len([cell for cell in stripped.strip("|").split("|")])
            if current_width is None:
                current_width = width
            self.assertEqual(width, current_width, msg=f"欄位數不一致：{line}")


def sample_rows():
    return [
        {
            "symbol": "2330.TW",
            "name": "台積電",
            "category": "watchlist",
            "status": "success",
            "sap_score": 95,
            "grade": "A",
            "piotroski_score": 9,
            "piotroski_total": 9,
            "reasonable_buy": 512.345,
            "first_target_price": 620.987,
            "missing_count": 0,
            "missing_fields": "",
            "data_quality_score": 100,
            "provider_source": "FinMind",
            "provider_fallback_used": False,
            "provider_fallback_reason": "",
        },
        {
            "symbol": "2454.TW",
            "name": "",
            "category": "watchlist",
            "status": "success",
            "sap_score": 70,
            "grade": "B",
            "piotroski_score": 7,
            "piotroski_total": 9,
            "reasonable_buy": None,
            "first_target_price": "",
            "missing_count": 2,
            "missing_fields": "current.revenue | previous.net_income",
            "data_quality_score": 90,
            "provider_source": "Yahoo Finance（FinMind fallback）",
            "provider_fallback_used": True,
            "provider_fallback_reason": "FinMind API error",
        },
    ]


def markdown_column_count(line: str) -> int:
    return len(line.strip().strip("|").split("|"))


if __name__ == "__main__":
    unittest.main()
