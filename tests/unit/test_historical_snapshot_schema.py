import unittest

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot, SnapshotMetadata
from historical.schema import HISTORICAL_SNAPSHOT_SCHEMA


class HistoricalSnapshotSchemaTests(unittest.TestCase):
    def test_financial_statement_snapshot_dataclass_can_be_created(self):
        snapshot = FinancialStatementSnapshot(
            symbol="2330.TW",
            fiscal_year=2025,
            fiscal_quarter=1,
            statement_date="2025-03-31",
            published_date="2025-05-15",
            snapshot_date="2025-06-30",
            source="fixture",
            source_version="v1",
            is_point_in_time=True,
            created_at="2026-01-01T00:00:00+00:00",
            statement_type="income_statement",
        )

        self.assertEqual(snapshot.symbol, "2330.TW")
        self.assertTrue(snapshot.is_point_in_time)

    def test_sap_score_snapshot_dataclass_can_be_created(self):
        snapshot = SAPScoreSnapshot(
            symbol="2330.TW",
            fiscal_year=2025,
            fiscal_quarter=1,
            statement_date="2025-03-31",
            published_date="2025-05-15",
            snapshot_date="2025-06-30",
            source="fixture",
            source_version="v1",
            is_point_in_time=True,
            created_at="2026-01-01T00:00:00+00:00",
            sap_score=90,
            piotroski_score=8,
            data_quality_score=100,
            credibility_grade="A",
            warning="",
        )

        self.assertEqual(snapshot.sap_score, 90)
        self.assertEqual(snapshot.credibility_grade, "A")

    def test_snapshot_metadata_dataclass_can_be_created(self):
        metadata = SnapshotMetadata(
            symbol="2330.TW",
            fiscal_year=2025,
            fiscal_quarter=1,
            statement_date="2025-03-31",
            published_date="2025-05-15",
            snapshot_date="2025-06-30",
            source="fixture",
            source_version="v1",
            is_point_in_time=True,
            created_at="2026-01-01T00:00:00+00:00",
            metadata={"run_id": "test"},
        )

        self.assertEqual(metadata.metadata["run_id"], "test")

    def test_schema_contains_required_tables(self):
        self.assertIn("CREATE TABLE IF NOT EXISTS financial_statement_snapshots", HISTORICAL_SNAPSHOT_SCHEMA)
        self.assertIn("CREATE TABLE IF NOT EXISTS sap_score_snapshots", HISTORICAL_SNAPSHOT_SCHEMA)
        self.assertIn("CREATE TABLE IF NOT EXISTS snapshot_metadata", HISTORICAL_SNAPSHOT_SCHEMA)

    def test_schema_contains_point_in_time_fields(self):
        for field_name in [
            "symbol",
            "fiscal_year",
            "fiscal_quarter",
            "statement_date",
            "published_date",
            "snapshot_date",
            "source",
            "source_version",
            "is_point_in_time",
            "created_at",
        ]:
            self.assertIn(field_name, HISTORICAL_SNAPSHOT_SCHEMA)

    def test_schema_contains_sap_score_snapshot_fields(self):
        for field_name in [
            "sap_score",
            "piotroski_score",
            "data_quality_score",
            "credibility_grade",
            "warning",
        ]:
            self.assertIn(field_name, HISTORICAL_SNAPSHOT_SCHEMA)


if __name__ == "__main__":
    unittest.main()
