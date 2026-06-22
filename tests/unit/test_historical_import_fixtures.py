import tempfile
import unittest
from pathlib import Path

from historical.repository import HistoricalSnapshotRepository
from historical_import import run_import


SAMPLE_ROOT = Path("tests/sample_data/historical")


class HistoricalImportFixtureTests(unittest.TestCase):
    def test_valid_sample_csv_files_can_import(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sap_db_path = temp_path / "sap_snapshots.db"
            financial_db_path = temp_path / "financial_snapshots.db"

            sap_summary = run_import(
                "sap",
                SAMPLE_ROOT / "sap_snapshots_valid.csv",
                db_path=sap_db_path,
                summary_path=temp_path / "sap_summary.md",
            )
            financial_summary = run_import(
                "financial",
                SAMPLE_ROOT / "financial_snapshots_valid.csv",
                db_path=financial_db_path,
                summary_path=temp_path / "financial_summary.md",
            )

            sap_repository = HistoricalSnapshotRepository(sap_db_path)
            financial_repository = HistoricalSnapshotRepository(financial_db_path)
            sap_symbols = sap_repository.list_symbols()
            financial_symbols = financial_repository.list_symbols()

            self.assertEqual(sap_summary.imported_count, 2)
            self.assertEqual(sap_summary.failed_count, 0)
            self.assertEqual(financial_summary.imported_count, 2)
            self.assertEqual(financial_summary.failed_count, 0)
            self.assertEqual(sap_symbols, ["1101.TW", "2308.TW"])
            self.assertEqual(financial_symbols, ["1101.TW", "2308.TW"])

    def test_invalid_sample_csv_files_fail_validation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            sap_summary = run_import(
                "sap",
                SAMPLE_ROOT / "sap_snapshots_invalid.csv",
                db_path=temp_path / "sap_invalid.db",
                summary_path=temp_path / "sap_invalid_summary.md",
            )
            financial_summary = run_import(
                "financial",
                SAMPLE_ROOT / "financial_snapshots_invalid.csv",
                db_path=temp_path / "financial_invalid.db",
                summary_path=temp_path / "financial_invalid_summary.md",
            )

        self.assertEqual(sap_summary.imported_count, 0)
        self.assertEqual(sap_summary.failed_count, 2)
        self.assertTrue(any("Missing required field: symbol" in error for error in sap_summary.errors))
        self.assertTrue(any("sap_score must be between 0 and 100" in error for error in sap_summary.errors))
        self.assertEqual(financial_summary.imported_count, 0)
        self.assertEqual(financial_summary.failed_count, 2)
        self.assertTrue(any("fiscal_quarter must be 1, 2, 3, or 4" in error for error in financial_summary.errors))
        self.assertTrue(any("Missing required field: statement_type" in error for error in financial_summary.errors))

    def test_summary_report_can_be_generated_from_sample_csv(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            summary_path = temp_path / "historical_import_summary.md"

            run_import(
                "sap",
                SAMPLE_ROOT / "sap_snapshots_valid.csv",
                db_path=temp_path / "summary.db",
                summary_path=summary_path,
            )
            content = summary_path.read_text(encoding="utf-8")

        self.assertIn("# Historical Import Summary", content)
        self.assertIn("| Imported Count | 2 |", content)
        self.assertIn("| Failed Count | 0 |", content)


if __name__ == "__main__":
    unittest.main()
