import os
import tempfile
import unittest
from pathlib import Path

from modules.report import generate_markdown_report


class ReportProviderSourceTests(unittest.TestCase):
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
        "valuation": {},
        "growth": {"score": 0, "max": 13, "items": []},
        "scoring": {"categories": {}},
    }


if __name__ == "__main__":
    unittest.main()
