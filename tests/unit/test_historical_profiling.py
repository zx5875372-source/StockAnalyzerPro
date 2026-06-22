import tempfile
import unittest
from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.profiling import (
    HistoricalProfiler,
    calculate_missing_percentage,
    calculate_point_in_time_percentage,
    calculate_quality_score,
)
from historical.profiling.profiler import write_data_quality_report
from historical.repository import HistoricalSnapshotRepository
from importers.import_result import ImportResult


class HistoricalProfilingTests(unittest.TestCase):
    def test_quality_score_calculation(self):
        score = calculate_quality_score(
            failed_rows=2,
            missing_field_count=3,
            duplicate_rows=1,
        )

        self.assertEqual(score, 69.0)

    def test_quality_score_has_zero_floor(self):
        score = calculate_quality_score(
            failed_rows=20,
            missing_field_count=20,
            duplicate_rows=20,
        )

        self.assertEqual(score, 0.0)

    def test_missing_percentage(self):
        self.assertEqual(calculate_missing_percentage(2, 4), 50.0)
        self.assertEqual(calculate_missing_percentage(0, 0), 0.0)

    def test_point_in_time_percentage(self):
        self.assertEqual(calculate_point_in_time_percentage(3, 4), 75.0)
        self.assertEqual(calculate_point_in_time_percentage(0, 0), 0.0)

    def test_profile_import_counts_missing_duplicate_and_point_in_time(self):
        import_result = ImportResult(
            importer="fixture",
            importer_version="v1",
            source="unit_test",
            imported_count=2,
            failed_count=1,
            sap_score_snapshots=[
                sap_snapshot(symbol="2330.TW", is_point_in_time=True),
                sap_snapshot(symbol="2454.TW", is_point_in_time=False),
            ],
            errors=["row 2: Missing required field: symbol"],
            warnings=["row 3: Duplicate historical snapshot key: ('2330.TW', 2025)"],
        )

        profile = HistoricalProfiler().profile_import(import_result)

        self.assertEqual(profile.total_rows, 3)
        self.assertEqual(profile.imported_rows, 2)
        self.assertEqual(profile.failed_rows, 1)
        self.assertEqual(profile.warning_rows, 1)
        self.assertEqual(profile.duplicate_rows, 1)
        self.assertEqual(profile.missing_field_count, 1)
        self.assertEqual(profile.missing_percentage, 33.33)
        self.assertEqual(profile.point_in_time_count, 1)
        self.assertEqual(profile.point_in_time_percentage, 50.0)
        self.assertEqual(profile.quality_score, 83.0)

    def test_profile_repository_duplicate_statistics(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot())
            repository.insert_financial_snapshot(financial_snapshot())

            profile = HistoricalProfiler().profile_repository(repository)

        self.assertEqual(profile.total_rows, 2)
        self.assertEqual(profile.imported_rows, 2)
        self.assertEqual(profile.duplicate_rows, 1)
        self.assertEqual(profile.point_in_time_count, 2)
        self.assertEqual(profile.point_in_time_percentage, 100.0)
        self.assertEqual(profile.quality_score, 95.0)

    def test_profile_repository_empty_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")

            profile = HistoricalProfiler().profile_repository(repository)

        self.assertEqual(profile.total_rows, 0)
        self.assertEqual(profile.imported_rows, 0)
        self.assertEqual(profile.failed_rows, 0)
        self.assertEqual(profile.warning_rows, 0)
        self.assertEqual(profile.duplicate_rows, 0)
        self.assertEqual(profile.missing_percentage, 0.0)
        self.assertEqual(profile.point_in_time_percentage, 0.0)
        self.assertEqual(profile.quality_score, 100.0)

    def test_write_data_quality_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "data_quality_report.md"
            profile = HistoricalProfiler().profile_import(
                ImportResult(
                    importer="fixture",
                    importer_version="v1",
                    source="unit_test",
                    imported_count=1,
                    sap_score_snapshots=[sap_snapshot()],
                )
            )

            write_data_quality_report(profile, output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assertIn("# Data Quality Report", content)
        self.assertIn("| Imported Rows | 1 |", content)
        self.assertIn("| Quality Score | 100.00 |", content)


def sap_snapshot(symbol="2330.TW", is_point_in_time=True):
    return SAPScoreSnapshot(
        symbol=symbol,
        fiscal_year=2025,
        fiscal_quarter=4,
        statement_date="2025-12-31",
        published_date="2026-03-31",
        snapshot_date="2026-04-01",
        source="fixture",
        source_version="v1",
        is_point_in_time=is_point_in_time,
        created_at="2026-04-01T00:00:00+00:00",
        sap_score=90,
        piotroski_score=8,
        data_quality_score=100,
        credibility_grade="A",
        warning="",
    )


def financial_snapshot():
    return FinancialStatementSnapshot(
        symbol="2330.TW",
        fiscal_year=2025,
        fiscal_quarter=4,
        statement_date="2025-12-31",
        published_date="2026-03-31",
        snapshot_date="2026-04-01",
        source="fixture",
        source_version="v1",
        is_point_in_time=True,
        created_at="2026-04-01T00:00:00+00:00",
        statement_type="income_statement",
        payload_json="{}",
        warning="",
    )


if __name__ == "__main__":
    unittest.main()
