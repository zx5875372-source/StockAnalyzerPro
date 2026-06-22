import tempfile
import unittest
from pathlib import Path

from historical.repository import HistoricalSnapshotRepository
from historical_generate_sap import run_generate
from historical_import import run_import


class HistoricalPipelineSmokeTests(unittest.TestCase):
    def test_pipeline_runs_end_to_end(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "historical_pipeline_test.db"
            import_summary_path = temp_path / "historical_import_summary.md"
            generator_summary_path = temp_path / "historical_generator_summary.md"

            import_summary = run_import(
                "financial",
                "tests/sample_data/historical/financial_snapshots_valid.csv",
                db_path=db_path,
                summary_path=import_summary_path,
            )
            generator_summary = run_generate(
                db_path=db_path,
                summary_path=generator_summary_path,
            )
            repository = HistoricalSnapshotRepository(db_path)
            financial_snapshots = repository.list_financial_snapshots()
            first_sap = repository.get_sap_snapshot("1101.TW", 2024, 4, "2025-03-21")
            second_sap = repository.get_sap_snapshot("2308.TW", 2024, 4, "2025-03-26")

        self.assertEqual(import_summary.imported_count, 2)
        self.assertEqual(generator_summary.generated, 2)
        self.assertEqual(generator_summary.failed, 0)
        self.assertEqual(len(financial_snapshots), 2)
        self.assertIsNotNone(first_sap)
        self.assertIsNotNone(second_sap)


if __name__ == "__main__":
    unittest.main()
