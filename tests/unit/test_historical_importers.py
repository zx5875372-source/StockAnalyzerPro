import tempfile
import unittest
from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from importers import (
    CSVHistoricalImporter,
    ImporterError,
    ImporterRegistry,
    ImporterRegistryError,
    MockImporter,
)


class ImporterRegistryTests(unittest.TestCase):
    def test_register_and_get_importer(self):
        registry = ImporterRegistry()
        registry.register("mock", MockImporter)

        importer = registry.get("mock")

        self.assertIsInstance(importer, MockImporter)

    def test_duplicate_register_raises_clear_error(self):
        registry = ImporterRegistry()
        registry.register("mock", MockImporter)

        with self.assertRaisesRegex(ImporterRegistryError, "already registered"):
            registry.register("mock", MockImporter)

    def test_get_unknown_importer_raises_clear_error(self):
        registry = ImporterRegistry()
        registry.register("mock", MockImporter)

        with self.assertRaisesRegex(ImporterRegistryError, "Unknown importer 'missing'.*mock"):
            registry.get("missing")

    def test_list_returns_registered_importer_names(self):
        registry = ImporterRegistry()
        registry.register("z-importer", MockImporter)
        registry.register("a-importer", MockImporter)

        self.assertEqual(registry.list(), ["a_importer", "z_importer"])

    def test_unregister_removes_importer(self):
        registry = ImporterRegistry()
        registry.register("mock", MockImporter)

        registry.unregister("mock")

        self.assertEqual(registry.list(), [])
        with self.assertRaisesRegex(ImporterRegistryError, "Unknown importer"):
            registry.get("mock")


class MockImporterTests(unittest.TestCase):
    def test_mock_importer_returns_configured_snapshots(self):
        importer = MockImporter(
            financial_statement_snapshots=[financial_snapshot()],
            sap_score_snapshots=[sap_snapshot()],
        )

        result = importer.import_snapshot("mock")

        self.assertEqual(result.importer, "mock")
        self.assertEqual(result.imported_count, 2)
        self.assertEqual(result.snapshot_count, 2)
        self.assertEqual(result.financial_statement_snapshots[0].symbol, "2330.TW")
        self.assertEqual(result.sap_score_snapshots[0].sap_score, 90)

    def test_mock_importer_supports_expected_snapshot_types(self):
        importer = MockImporter()

        self.assertTrue(importer.supports("financial_statement"))
        self.assertTrue(importer.supports("sap_score"))
        self.assertFalse(importer.supports("unknown"))


class CSVHistoricalImporterTests(unittest.TestCase):
    def test_csv_importer_reads_financial_statement_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "financial.csv"
            csv_path.write_text(financial_csv(), encoding="utf-8")

            result = CSVHistoricalImporter().import_financial_statements(csv_path)

        self.assertEqual(result.imported_count, 1)
        self.assertEqual(result.failed_count, 0)
        snapshot = result.financial_statement_snapshots[0]
        self.assertIsInstance(snapshot, FinancialStatementSnapshot)
        self.assertEqual(snapshot.symbol, "2330.TW")
        self.assertTrue(snapshot.is_point_in_time)
        self.assertEqual(snapshot.statement_type, "income_statement")

    def test_csv_importer_reads_sap_score_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sap.csv"
            csv_path.write_text(sap_csv(), encoding="utf-8")

            result = CSVHistoricalImporter().import_snapshot(csv_path, snapshot_type="sap_score")

        self.assertEqual(result.imported_count, 1)
        self.assertEqual(result.failed_count, 0)
        snapshot = result.sap_score_snapshots[0]
        self.assertIsInstance(snapshot, SAPScoreSnapshot)
        self.assertEqual(snapshot.symbol, "2330.TW")
        self.assertFalse(snapshot.is_point_in_time)
        self.assertEqual(snapshot.sap_score, 90)
        self.assertEqual(snapshot.warning, "not_point_in_time")
        self.assertEqual(result.errors, [])
        self.assertEqual(result.warnings, [])

    def test_csv_importer_rejects_missing_required_field_value(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sap_missing_field.csv"
            csv_path.write_text(sap_csv(symbol="", sap_score=""), encoding="utf-8")

            result = CSVHistoricalImporter().import_snapshot(csv_path, snapshot_type="sap_score")

        self.assertEqual(result.imported_count, 0)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.sap_score_snapshots, [])
        self.assertTrue(any("Missing required field: symbol" in error for error in result.errors))
        self.assertTrue(any("Missing required field: sap_score" in error for error in result.errors))

    def test_csv_importer_rejects_invalid_score(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sap_invalid_score.csv"
            csv_path.write_text(sap_csv(sap_score="120"), encoding="utf-8")

            result = CSVHistoricalImporter().import_snapshot(csv_path, snapshot_type="sap_score")

        self.assertEqual(result.imported_count, 0)
        self.assertEqual(result.failed_count, 1)
        self.assertEqual(result.sap_score_snapshots, [])
        self.assertTrue(any("sap_score must be between 0 and 100: 120.0" in error for error in result.errors))

    def test_csv_importer_records_warning_and_still_imports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sap_duplicate.csv"
            csv_path.write_text(sap_csv_with_duplicate(), encoding="utf-8")

            result = CSVHistoricalImporter().import_snapshot(csv_path, snapshot_type="sap_score")

        self.assertEqual(result.imported_count, 2)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(len(result.sap_score_snapshots), 2)
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("Duplicate historical snapshot key", result.warnings[0])

    def test_csv_importer_infers_sap_score_snapshot_type(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sap.csv"
            csv_path.write_text(sap_csv(), encoding="utf-8")

            result = CSVHistoricalImporter().import_snapshot(csv_path)

        self.assertEqual(len(result.sap_score_snapshots), 1)

    def test_csv_importer_rejects_missing_required_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "bad.csv"
            csv_path.write_text("symbol,sap_score\n2330,90\n", encoding="utf-8")

            with self.assertRaisesRegex(ImporterError, "missing required columns"):
                CSVHistoricalImporter().import_snapshot(csv_path, snapshot_type="sap_score")

    def test_csv_importer_accepts_validator_hook_without_changing_flow(self):
        validator = object()
        importer = CSVHistoricalImporter(validator=validator)

        self.assertIs(importer.validator, validator)


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


def sap_snapshot():
    return SAPScoreSnapshot(
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
        sap_score=90,
        piotroski_score=8,
        data_quality_score=100,
        credibility_grade="A",
        warning="",
    )


def financial_csv():
    return "\n".join(
        [
            "symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,statement_type,payload_json,warning",
            "2330,2025,4,2025-12-31,2026-03-31,2026-04-01,fixture,v1,true,2026-04-01T00:00:00+00:00,income_statement,{},",
            "",
        ]
    )


def sap_csv(symbol="2330", sap_score="90"):
    return "\n".join(
        [
            "symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,sap_score,piotroski_score,data_quality_score,credibility_grade,warning",
            f"{symbol},2025,4,2025-12-31,2026-03-31,2026-04-01,current_analysis_proxy,v0,false,2026-04-01T00:00:00+00:00,{sap_score},8,100,C,not_point_in_time",
            "",
        ]
    )


def sap_csv_with_duplicate():
    return "\n".join(
        [
            "symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,sap_score,piotroski_score,data_quality_score,credibility_grade,warning",
            "2330,2025,4,2025-12-31,2026-03-31,2026-04-01,current_analysis_proxy,v0,false,2026-04-01T00:00:00+00:00,90,8,100,C,not_point_in_time",
            "2330,2025,4,2025-12-31,2026-03-31,2026-04-01,current_analysis_proxy,v0,false,2026-04-01T00:00:00+00:00,91,8,100,C,not_point_in_time",
            "",
        ]
    )


if __name__ == "__main__":
    unittest.main()
