import unittest

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.validation import HistoricalValidator, ValidationResult


class HistoricalValidationTests(unittest.TestCase):
    def test_valid_sap_snapshot(self):
        validator = HistoricalValidator()

        result = validator.validate_sap_snapshot(sap_snapshot())

        self.assertIsInstance(result, ValidationResult)
        self.assertTrue(result.is_valid)
        self.assertEqual(result.errors, [])
        self.assertEqual(result.missing_fields, [])
        self.assertEqual(result.field_count, 10)

    def test_missing_fields_are_reported(self):
        validator = HistoricalValidator()
        snapshot = sap_snapshot(symbol="", sap_score=None)

        result = validator.validate_sap_snapshot(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("symbol", result.missing_fields)
        self.assertIn("sap_score", result.missing_fields)
        self.assertIn("Missing required field: symbol", result.errors)
        self.assertIn("Missing required field: sap_score", result.errors)

    def test_invalid_dates_are_reported(self):
        validator = HistoricalValidator()
        snapshot = sap_snapshot(
            published_date="2026-05-01",
            snapshot_date="2026-04-01",
        )

        result = validator.validate_sap_snapshot(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("published_date must be on or before snapshot_date", result.errors)

    def test_invalid_date_format_is_reported(self):
        validator = HistoricalValidator()
        snapshot = financial_snapshot(snapshot_date="20260401")

        result = validator.validate_financial_snapshot(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("snapshot_date must be an ISO date: 20260401", result.errors)

    def test_score_range_is_reported(self):
        validator = HistoricalValidator()
        snapshot = sap_snapshot(sap_score=120, piotroski_score=10, data_quality_score=-1)

        result = validator.validate_sap_snapshot(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("sap_score must be between 0 and 100: 120", result.errors)
        self.assertIn("piotroski_score must be between 0 and 9: 10", result.errors)
        self.assertIn("data_quality_score must be between 0 and 100: -1", result.errors)

    def test_invalid_credibility_grade_is_reported(self):
        validator = HistoricalValidator()
        snapshot = sap_snapshot(credibility_grade="Z")

        result = validator.validate_sap_snapshot(snapshot)

        self.assertFalse(result.is_valid)
        self.assertIn("credibility_grade must be one of A, B, C, D: Z", result.errors)

    def test_duplicate_snapshot_adds_warning(self):
        validator = HistoricalValidator()
        snapshot = sap_snapshot()

        first_result = validator.validate_sap_snapshot(snapshot)
        second_result = validator.validate_sap_snapshot(snapshot)

        self.assertTrue(first_result.is_valid)
        self.assertTrue(second_result.is_valid)
        self.assertEqual(first_result.warnings, [])
        self.assertEqual(len(second_result.warnings), 1)
        self.assertIn("Duplicate historical snapshot key", second_result.warnings[0])


def sap_snapshot(**overrides):
    values = {
        "symbol": "2330.TW",
        "fiscal_year": 2025,
        "fiscal_quarter": 4,
        "statement_date": "2025-12-31",
        "published_date": "2026-03-31",
        "snapshot_date": "2026-04-01",
        "source": "fixture",
        "source_version": "v1",
        "is_point_in_time": True,
        "created_at": "2026-04-01T00:00:00+00:00",
        "sap_score": 90,
        "piotroski_score": 8,
        "data_quality_score": 100,
        "credibility_grade": "A",
        "warning": "",
    }
    values.update(overrides)
    return SAPScoreSnapshot(**values)


def financial_snapshot(**overrides):
    values = {
        "symbol": "2330.TW",
        "fiscal_year": 2025,
        "fiscal_quarter": 4,
        "statement_date": "2025-12-31",
        "published_date": "2026-03-31",
        "snapshot_date": "2026-04-01",
        "source": "fixture",
        "source_version": "v1",
        "is_point_in_time": True,
        "created_at": "2026-04-01T00:00:00+00:00",
        "statement_type": "income_statement",
        "payload_json": "{}",
        "warning": "",
    }
    values.update(overrides)
    return FinancialStatementSnapshot(**values)


if __name__ == "__main__":
    unittest.main()
