from contextlib import redirect_stderr
from io import StringIO
import tempfile
import unittest
from pathlib import Path

from historical.repository import HistoricalSnapshotRepository
from historical_import import main, run_import


class HistoricalImportCliTests(unittest.TestCase):
    def test_sap_csv_imports_into_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = temp_path / "sap.csv"
            db_path = temp_path / "historical_snapshots.db"
            summary_path = temp_path / "historical_import_summary.md"
            csv_path.write_text(sap_csv(), encoding="utf-8")

            summary = run_import("sap", csv_path, db_path=db_path, summary_path=summary_path)
            repository = HistoricalSnapshotRepository(db_path)
            snapshot = repository.get_sap_snapshot("2330.TW", 2025, 4, "2026-04-01")

        self.assertEqual(summary.imported_count, 1)
        self.assertEqual(summary.failed_count, 0)
        self.assertEqual(summary.warning_count, 0)
        self.assertEqual(summary.errors, [])
        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.sap_score, 90)

    def test_invalid_csv_fails_without_repository_write(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = temp_path / "sap_invalid.csv"
            db_path = temp_path / "historical_snapshots.db"
            summary_path = temp_path / "historical_import_summary.md"
            csv_path.write_text(sap_csv(sap_score="120"), encoding="utf-8")

            summary = run_import("sap", csv_path, db_path=db_path, summary_path=summary_path)
            repository = HistoricalSnapshotRepository(db_path)
            snapshot = repository.get_sap_snapshot("2330.TW", 2025, 4, "2026-04-01")

        self.assertEqual(summary.imported_count, 0)
        self.assertEqual(summary.failed_count, 1)
        self.assertIsNone(snapshot)
        self.assertTrue(any("sap_score must be between 0 and 100" in error for error in summary.errors))

    def test_warnings_still_import(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = temp_path / "financial_duplicate.csv"
            db_path = temp_path / "historical_snapshots.db"
            summary_path = temp_path / "historical_import_summary.md"
            csv_path.write_text(financial_duplicate_csv(), encoding="utf-8")

            summary = run_import("financial", csv_path, db_path=db_path, summary_path=summary_path)
            repository = HistoricalSnapshotRepository(db_path)
            snapshot = repository.get_financial_snapshot(
                "2330.TW",
                2025,
                4,
                "2026-04-01",
                statement_type="income_statement",
            )

        self.assertEqual(summary.imported_count, 2)
        self.assertEqual(summary.failed_count, 0)
        self.assertEqual(summary.warning_count, 1)
        self.assertTrue(any("Duplicate historical snapshot key" in warning for warning in summary.warnings))
        self.assertIsNotNone(snapshot)

    def test_summary_markdown_is_written(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            csv_path = temp_path / "sap.csv"
            db_path = temp_path / "historical_snapshots.db"
            summary_path = temp_path / "historical_import_summary.md"
            csv_path.write_text(sap_csv(), encoding="utf-8")

            run_import("sap", csv_path, db_path=db_path, summary_path=summary_path)
            content = summary_path.read_text(encoding="utf-8")

        self.assertIn("# Historical Import Summary", content)
        self.assertIn("| Imported Count | 1 |", content)
        self.assertIn("| Failed Count | 0 |", content)

    def test_cli_missing_file_has_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            missing_path = temp_path / "missing.csv"
            db_path = temp_path / "historical_snapshots.db"
            stderr = StringIO()

            with redirect_stderr(stderr):
                exit_code = main(["--type", "sap", "--file", str(missing_path), "--db", str(db_path)])

        self.assertEqual(exit_code, 1)
        self.assertIn("ERROR: Historical import CSV not found", stderr.getvalue())
        self.assertIn(str(missing_path), stderr.getvalue())


def sap_csv(sap_score="90"):
    return "\n".join(
        [
            "symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,sap_score,piotroski_score,data_quality_score,credibility_grade,warning",
            f"2330,2025,4,2025-12-31,2026-03-31,2026-04-01,fixture,v1,true,2026-04-01T00:00:00+00:00,{sap_score},8,100,A,",
            "",
        ]
    )


def financial_duplicate_csv():
    return "\n".join(
        [
            "symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,statement_type,payload_json,warning",
            "2330,2025,4,2025-12-31,2026-03-31,2026-04-01,fixture,v1,true,2026-04-01T00:00:00+00:00,income_statement,{},",
            "2330,2025,4,2025-12-31,2026-03-31,2026-04-01,fixture,v1,true,2026-04-01T00:00:00+00:00,income_statement,{},",
            "",
        ]
    )


if __name__ == "__main__":
    unittest.main()
