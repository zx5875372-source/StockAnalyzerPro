import json
import unittest

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from importers.finmind import (
    FINMIND_SOURCE,
    FINMIND_SOURCE_VERSION,
    FinMindMappingError,
    map_financial_statement_row,
    map_sap_snapshot_row,
)


class FinMindMapperTests(unittest.TestCase):
    def test_valid_financial_row_maps_to_snapshot(self):
        snapshot = map_financial_statement_row(
            {
                "stock_id": "2330",
                "date": "2024-12-31",
                "year": "2024",
                "quarter": "Q4",
                "release_date": "2025-03-20",
                "statement_type": "income_statement",
                "revenue": 2500,
                "net_income": 900,
                "created_at": "2025-03-21T00:00:00+00:00",
            }
        )

        self.assertIsInstance(snapshot, FinancialStatementSnapshot)
        self.assertEqual(snapshot.symbol, "2330.TW")
        self.assertEqual(snapshot.fiscal_year, 2024)
        self.assertEqual(snapshot.fiscal_quarter, 4)
        self.assertEqual(snapshot.statement_date, "2024-12-31")
        self.assertEqual(snapshot.published_date, "2025-03-20")
        self.assertEqual(snapshot.snapshot_date, "2025-03-20")
        self.assertEqual(snapshot.source, FINMIND_SOURCE)
        self.assertEqual(snapshot.source_version, FINMIND_SOURCE_VERSION)
        self.assertTrue(snapshot.is_point_in_time)
        self.assertEqual(snapshot.statement_type, "income_statement")
        self.assertEqual(json.loads(snapshot.payload_json), {"net_income": 900, "revenue": 2500})

    def test_financial_row_missing_published_date_falls_back_to_statement_date(self):
        snapshot = map_financial_statement_row(
            {
                "stock_id": "2330",
                "date": "2024-12-31",
                "year": "2024",
                "quarter": "Q4",
                "statement_type": "income_statement",
                "revenue": 2500,
            }
        )

        self.assertEqual(snapshot.published_date, "2024-12-31")
        self.assertEqual(snapshot.snapshot_date, "2024-12-31")
        self.assertFalse(snapshot.is_point_in_time)
        self.assertIn("missing_published_date", snapshot.warning)

    def test_valid_sap_row_maps_to_snapshot(self):
        snapshot = map_sap_snapshot_row(
            {
                "symbol": "2454",
                "statement_date": "2024-09-30",
                "fiscal_year": 2024,
                "fiscal_quarter": 3,
                "published_date": "2024-11-14",
                "snapshot_date": "2024-11-15",
                "sap_score": "88",
                "piotroski_score": "8",
                "data_quality_score": "95",
                "credibility_grade": "A",
                "created_at": "2024-11-15T00:00:00+00:00",
            }
        )

        self.assertIsInstance(snapshot, SAPScoreSnapshot)
        self.assertEqual(snapshot.symbol, "2454.TW")
        self.assertEqual(snapshot.fiscal_year, 2024)
        self.assertEqual(snapshot.fiscal_quarter, 3)
        self.assertEqual(snapshot.statement_date, "2024-09-30")
        self.assertEqual(snapshot.published_date, "2024-11-14")
        self.assertEqual(snapshot.snapshot_date, "2024-11-15")
        self.assertEqual(snapshot.source, "finmind")
        self.assertEqual(snapshot.source_version, "v1")
        self.assertTrue(snapshot.is_point_in_time)
        self.assertEqual(snapshot.sap_score, 88.0)
        self.assertEqual(snapshot.piotroski_score, 8.0)
        self.assertEqual(snapshot.data_quality_score, 95.0)
        self.assertEqual(snapshot.credibility_grade, "A")

    def test_missing_required_fields_raise_clear_error(self):
        with self.assertRaisesRegex(FinMindMappingError, "Missing required FinMind field: symbol, stock_id"):
            map_financial_statement_row(
                {
                    "date": "2024-12-31",
                    "release_date": "2025-03-20",
                    "statement_type": "income_statement",
                }
            )

        with self.assertRaisesRegex(FinMindMappingError, "Missing required FinMind field: sap_score"):
            map_sap_snapshot_row(
                {
                    "stock_id": "2330",
                    "date": "2024-12-31",
                    "release_date": "2025-03-20",
                    "piotroski_score": 8,
                    "data_quality_score": 90,
                    "credibility_grade": "B",
                }
            )

    def test_date_conversion_supports_republic_year(self):
        snapshot = map_financial_statement_row(
            {
                "stock_id": "2330",
                "date": "113-12-31",
                "year": "113",
                "release_date": "114/03/20",
                "statement_type": "balance_sheet",
            }
        )

        self.assertEqual(snapshot.fiscal_year, 2024)
        self.assertEqual(snapshot.statement_date, "2024-12-31")
        self.assertEqual(snapshot.published_date, "2025-03-20")

    def test_quarter_mapping_from_statement_date(self):
        first_quarter = map_financial_statement_row(financial_row(date="2024-03-31"))
        second_quarter = map_financial_statement_row(financial_row(date="2024-06-30"))
        third_quarter = map_financial_statement_row(financial_row(date="2024-09-30"))
        fourth_quarter = map_financial_statement_row(financial_row(date="2024-12-31"))

        self.assertEqual(first_quarter.fiscal_quarter, 1)
        self.assertEqual(second_quarter.fiscal_quarter, 2)
        self.assertEqual(third_quarter.fiscal_quarter, 3)
        self.assertEqual(fourth_quarter.fiscal_quarter, 4)


def financial_row(date):
    return {
        "stock_id": "2330",
        "date": date,
        "release_date": "2025-03-20",
        "statement_type": "income_statement",
    }


if __name__ == "__main__":
    unittest.main()
