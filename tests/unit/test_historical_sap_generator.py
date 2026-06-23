import json
import tempfile
import unittest
from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.repository import HistoricalSnapshotRepository
from historical.sap_generator import HistoricalSAPGenerator


class HistoricalSAPGeneratorTests(unittest.TestCase):
    def test_single_snapshot_generation(self):
        generator = HistoricalSAPGenerator()

        snapshot = generator.generate_snapshot(financial_snapshot())

        self.assertIsInstance(snapshot, SAPScoreSnapshot)
        self.assertEqual(snapshot.symbol, "2330.TW")
        self.assertEqual(snapshot.fiscal_year, 2025)
        self.assertEqual(snapshot.fiscal_quarter, 1)
        self.assertEqual(snapshot.sap_score, 100)
        self.assertEqual(snapshot.piotroski_score, 9)
        self.assertEqual(snapshot.data_quality_score, 100)
        self.assertEqual(snapshot.credibility_grade, "A")
        self.assertTrue(snapshot.is_point_in_time)
        self.assertEqual(snapshot.warning, "")

    def test_multiple_snapshot_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = HistoricalSnapshotRepository(temp_path / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot(symbol="2330.TW"))
            repository.insert_financial_snapshot(financial_snapshot(symbol="2454.TW"))
            generator = HistoricalSAPGenerator(
                repository=repository,
                summary_path=temp_path / "historical_generator_summary.md",
            )

            result = generator.generate_all()

        self.assertEqual(result.generated, 2)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.failed, 0)
        self.assertEqual(len(result.snapshots), 2)

    def test_duplicate_update(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = HistoricalSnapshotRepository(temp_path / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot())
            repository.insert_sap_snapshot(existing_sap_snapshot())
            generator = HistoricalSAPGenerator(
                repository=repository,
                summary_path=temp_path / "historical_generator_summary.md",
            )

            result = generator.generate_all()
            snapshot = repository.get_sap_snapshot("2330.TW", 2025, 1, "2025-06-30")

        self.assertEqual(result.generated, 0)
        self.assertEqual(result.updated, 1)
        self.assertEqual(result.failed, 0)
        self.assertEqual(snapshot.sap_score, 100)
        self.assertEqual(snapshot.credibility_grade, "A")

    def test_repository_integration_writes_sap_snapshot_and_summary(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = HistoricalSnapshotRepository(temp_path / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot())
            summary_path = temp_path / "historical_generator_summary.md"
            generator = HistoricalSAPGenerator(repository=repository, summary_path=summary_path)

            result = generator.generate_all()
            snapshot = repository.get_sap_snapshot("2330.TW", 2025, 1, "2025-06-30")
            summary_content = summary_path.read_text(encoding="utf-8")

        self.assertEqual(result.generated, 1)
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.sap_score, 100)
        self.assertIn("| Generated | 1 |", summary_content)
        self.assertIn("| Updated | 0 |", summary_content)
        self.assertIn("| Failed | 0 |", summary_content)
        self.assertIn("| Warnings | 0 |", summary_content)

    def test_incremental_generation_skips_unchanged_period(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = HistoricalSnapshotRepository(temp_path / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot())
            generator = HistoricalSAPGenerator(
                repository=repository,
                summary_path=temp_path / "historical_generator_summary.md",
            )
            generator.generate_all()

            result = generator.generate_incremental()

        self.assertEqual(result.generated, 0)
        self.assertEqual(result.updated, 0)
        self.assertEqual(result.skipped, 1)
        self.assertEqual(result.affected_periods, [])

    def test_incremental_generation_updates_old_generator_version(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = HistoricalSnapshotRepository(temp_path / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot())
            repository.insert_sap_snapshot(existing_sap_snapshot(source_version="v0"))
            generator = HistoricalSAPGenerator(
                repository=repository,
                summary_path=temp_path / "historical_generator_summary.md",
            )

            result = generator.generate_incremental()

        self.assertEqual(result.generated, 0)
        self.assertEqual(result.updated, 1)
        self.assertEqual(result.skipped, 0)
        self.assertIn("generator_version_changed", result.affected_periods[0])

    def test_incremental_generation_warns_on_publication_timeline_change(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = HistoricalSnapshotRepository(temp_path / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot(published_date="2025-05-20"))
            repository.insert_sap_snapshot(existing_sap_snapshot(published_date="2025-05-15"))
            generator = HistoricalSAPGenerator(
                repository=repository,
                summary_path=temp_path / "historical_generator_summary.md",
            )

            result = generator.generate_incremental()

        self.assertEqual(result.updated, 1)
        self.assertTrue(any("publication_timeline_changed" in warning for warning in result.warnings))


def financial_snapshot(symbol="2330.TW", published_date="2025-05-15"):
    return FinancialStatementSnapshot(
        symbol=symbol,
        fiscal_year=2025,
        fiscal_quarter=1,
        statement_date="2025-03-31",
        published_date=published_date,
        snapshot_date="2025-06-30",
        source="fixture",
        source_version="v1",
        is_point_in_time=True,
        created_at="2026-01-01T00:00:00+00:00",
        statement_type="income_statement",
        payload_json=json.dumps(sample_payload()),
        warning="",
    )


def existing_sap_snapshot(source_version="v1", published_date="2025-05-15"):
    return SAPScoreSnapshot(
        symbol="2330.TW",
        fiscal_year=2025,
        fiscal_quarter=1,
        statement_date="2025-03-31",
        published_date=published_date,
        snapshot_date="2025-06-30",
        source="fixture",
        source_version=source_version,
        is_point_in_time=True,
        created_at="2026-01-01T00:00:00+00:00",
        sap_score=70,
        piotroski_score=6,
        data_quality_score=80,
        credibility_grade="B",
        warning="",
    )


def sample_payload():
    return {
        "price": 100,
        "pe": 10,
        "pb": 1.5,
        "current": {
            "net_income": 120,
            "total_assets": 1000,
            "total_equity": 500,
            "total_debt": 100,
            "long_term_debt": 100,
            "current_assets": 300,
            "current_liabilities": 100,
            "revenue": 1200,
            "gross_profit": 600,
            "operating_income": 200,
            "operating_cashflow": 150,
            "free_cashflow": 80,
            "shares_outstanding": 10,
            "eps": 12,
            "book_value_per_share": 50,
        },
        "previous": {
            "net_income": 80,
            "total_assets": 900,
            "total_equity": 450,
            "total_debt": 120,
            "long_term_debt": 120,
            "current_assets": 200,
            "current_liabilities": 100,
            "revenue": 1000,
            "gross_profit": 450,
            "operating_income": 150,
            "operating_cashflow": 90,
            "free_cashflow": 40,
            "shares_outstanding": 11,
            "eps": 8,
            "book_value_per_share": 45,
        },
    }


if __name__ == "__main__":
    unittest.main()
