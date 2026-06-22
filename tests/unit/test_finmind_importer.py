import tempfile
import unittest
from pathlib import Path

from historical.repository import HistoricalSnapshotRepository
from importers import FinMindImporter
from importers.finmind import FinMindAPIError, FinMindResponse
from importers.registry import create_default_registry


class MockFinMindClient:
    def __init__(self, response=None, error=None):
        self.response = response or FinMindResponse(status=200, message="success", data=[])
        self.error = error
        self.calls = []

    def get_financial_statement(self, stock_id, start_date=None, end_date=None):
        self.calls.append(
            {
                "stock_id": stock_id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        if self.error:
            raise self.error
        return self.response


class FinMindImporterTests(unittest.TestCase):
    def test_default_registry_has_finmind(self):
        registry = create_default_registry()

        self.assertIn("finmind", registry.list())
        self.assertIsInstance(registry.get("finmind"), FinMindImporter)

    def test_importer_metadata(self):
        importer = FinMindImporter()

        self.assertEqual(importer.name, "finmind")
        self.assertEqual(importer.version, "v1-integration")

    def test_supports_planned_snapshot_types(self):
        importer = FinMindImporter()

        self.assertTrue(importer.supports("financial"))
        self.assertTrue(importer.supports("financial_statement"))
        self.assertTrue(importer.supports("sap"))
        self.assertTrue(importer.supports("sap_score"))
        self.assertFalse(importer.supports("price_history"))
        self.assertFalse(importer.supports("unknown"))

    def test_valid_response_writes_to_repository(self):
        client = MockFinMindClient(
            response=FinMindResponse(
                status=200,
                message="success",
                data=[valid_financial_row()],
            )
        )
        importer = FinMindImporter(client=client)

        with temp_repository() as repository:
            result = importer.import_financial_statements(
                "2330",
                start_date="2025-01-01",
                end_date="2025-12-31",
                repository=repository,
            )

            snapshot = repository.get_financial_snapshot("2330.TW", 2025, 1, "2025-03-21", "income_statement")

        self.assertEqual(result.imported_count, 1)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.errors, [])
        self.assertEqual(snapshot.symbol, "2330.TW")
        self.assertEqual(client.calls[0]["stock_id"], "2330")
        self.assertEqual(client.calls[0]["start_date"], "2025-01-01")
        self.assertEqual(client.calls[0]["end_date"], "2025-12-31")

    def test_missing_published_date_row_writes_with_warning(self):
        row = valid_financial_row()
        row.pop("release_date")
        row.pop("snapshot_date")
        importer = FinMindImporter(
            client=MockFinMindClient(
                response=FinMindResponse(status=200, message="success", data=[row])
            )
        )

        with temp_repository() as repository:
            result = importer.import_financial_statements("2330", repository=repository)
            snapshot = repository.get_financial_snapshot("2330.TW", 2025, 1, "2025-03-31", "income_statement")

        self.assertEqual(result.imported_count, 1)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.errors, [])
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("missing_published_date", result.warnings[0])
        self.assertIsNotNone(snapshot)
        self.assertFalse(snapshot.is_point_in_time)
        self.assertIn("missing_published_date", snapshot.warning)

    def test_invalid_row_does_not_write_to_repository(self):
        row = valid_financial_row()
        row["published_date"] = "2025-03-22"
        row["snapshot_date"] = "2025-03-21"
        importer = FinMindImporter(
            client=MockFinMindClient(
                response=FinMindResponse(status=200, message="success", data=[row])
            )
        )

        with temp_repository() as repository:
            result = importer.import_financial_statements("2330", repository=repository)
            symbols = repository.list_symbols()

        self.assertEqual(result.imported_count, 0)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(symbols, [])
        self.assertTrue(any("published_date must be on or before snapshot_date" in error for error in result.errors))

    def test_warning_row_still_writes_to_repository(self):
        row = valid_financial_row()
        importer = FinMindImporter(
            client=MockFinMindClient(
                response=FinMindResponse(status=200, message="success", data=[row, dict(row)])
            )
        )

        with temp_repository() as repository:
            result = importer.import_financial_statements("2330", repository=repository)
            symbols = repository.list_symbols()

        self.assertEqual(result.imported_count, 2)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(symbols, ["2330.TW"])
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Duplicate historical snapshot key", result.warnings[0])

    def test_api_error_returns_failed_import_result(self):
        importer = FinMindImporter(
            client=MockFinMindClient(error=FinMindAPIError("service unavailable"))
        )

        with temp_repository() as repository:
            result = importer.import_financial_statements("2330", repository=repository)
            symbols = repository.list_symbols()

        self.assertEqual(result.imported_count, 0)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(symbols, [])
        self.assertIn("FinMind API error for 2330", result.errors[0])

    def test_sap_snapshot_import_is_not_implemented_yet(self):
        importer = FinMindImporter(client=MockFinMindClient())

        with self.assertRaisesRegex(NotImplementedError, "SAP score snapshot import"):
            importer.import_snapshot("2330", snapshot_type="sap")


def valid_financial_row():
    return {
        "stock_id": "2330",
        "date": "2025-03-31",
        "year": "2025",
        "quarter": "1",
        "release_date": "2025-03-21",
        "snapshot_date": "2025-03-21",
        "statement_type": "income_statement",
        "created_at": "2025-03-21T00:00:00+00:00",
        "Revenue": 1000,
        "GrossProfit": 600,
    }


class temp_repository:
    def __enter__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self._temp_dir.name) / "historical_snapshots.db"
        self.repository = HistoricalSnapshotRepository(db_path)
        return self.repository

    def __exit__(self, exc_type, exc_value, traceback):
        self._temp_dir.cleanup()


if __name__ == "__main__":
    unittest.main()
