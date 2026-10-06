"""Characterization tests: the rendered Markdown report must stay byte-identical.

Regenerate the golden files only for an intentional output change:
    UPDATE_REPORT_GOLDEN=1 python -m unittest tests.unit.test_report_golden
"""

import copy
import os
import unittest
from pathlib import Path

from tests.unit.test_report_provider_source import (
    piotroski_items,
    render_report,
    sample_industry_ranking,
    sample_result,
    sample_technical,
)

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "sample_data" / "report_golden"


def minimal_result():
    return sample_result()


def full_result():
    result = sample_result()
    result["industry"] = "Semiconductors"
    result["sector"] = "Technology"
    result["piotroski"] = {"score": 5, "available": 8, "total": 9, "items": piotroski_items()}
    result["technical"] = sample_technical()
    result["industry_ranking"] = sample_industry_ranking()
    result["valuation"].update(
        {"valuation_profile": "半導體", "pe_range": [15.0, 25.5], "pb_range": [2, 4.25]}
    )
    result["growth"] = {
        "score": 8,
        "max": 13,
        "items": [
            {"name": "營收成長", "growth_rate": 0.1234, "score": 5, "max": 5, "note": "營收成長佳"},
            {"name": "EPS 成長", "growth_rate": -0.05, "score": 0, "max": 5, "note": "EPS 衰退"},
            {"name": "自由現金流成長", "growth_rate": 0.5, "score": 3, "max": 3, "note": "FCF 成長"},
        ],
    }
    result["scoring"] = {
        "categories": {
            "profitability": {
                "score": 18,
                "max": 20,
                "items": [
                    {"name": "ROE", "score": 12, "max": 12, "note": "ROE 高"},
                    {"name": "ROA", "score": 6, "max": 8, "note": "ROA 佳"},
                ],
            },
            "growth": {"score": 0, "max": 13, "items": ["營收成長"]},
        }
    }
    result["diagnostics"] = [
        "still_missing_fields: current.total_assets, dividend",
        "yahoo_enriched_fields: price",
        "provider_selected_provider: FinMind",
        "valuation_profile: 半導體",
        "PE 資料來源不完整",
    ]
    result["reasons"] = ["估值偏高", "現金流穩定"]
    return result


def fallback_result():
    result = sample_result()
    result["provider_source"] = "Yahoo Finance (fallback)"
    result["provider_fallback_used"] = True
    result["provider_fallback_reason"] = "FinMind timeout"
    result["price"] = None
    result["industry"] = None
    result["sector"] = ""
    result["grade"] = "C級"
    result["sap_score"] = 45
    result["free_cashflow"] = -10
    result["operating_cashflow"] = -20
    result["pe"] = None
    result["roe"] = 12.345
    result["missing_fields"] = ["dividend"]
    result["diagnostics"] = ["technical_source: none", "some_note: x"]
    result["technical"] = {"trend_score": None, "diagnostics": []}
    result["growth"] = {
        "score": 2,
        "max": 13,
        "items": [{"name": "營收成長", "growth_rate": None, "score": 2, "max": 5, "note": "資料不足"}],
    }
    return result


CASES = {
    "minimal": minimal_result,
    "full": full_result,
    "fallback": fallback_result,
}


class ReportGoldenTests(unittest.TestCase):
    def test_reports_match_golden_files(self):
        update = os.environ.get("UPDATE_REPORT_GOLDEN") == "1"
        for name, factory in CASES.items():
            with self.subTest(case=name):
                content = render_report(copy.deepcopy(factory()))
                golden_path = GOLDEN_DIR / f"{name}.md"
                if update:
                    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
                    golden_path.write_bytes(content.encode("utf-8"))
                    continue
                # read_text normalizes line endings, so git autocrlf cannot break the comparison.
                expected = golden_path.read_text(encoding="utf-8")
                self.assertEqual(content, expected)


if __name__ == "__main__":
    unittest.main()
