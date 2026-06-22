from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.repository import HistoricalSnapshotRepository


class HistoricalSnapshotRepositoryTests(unittest.TestCase):
    def test_initialize_schema_creates_tables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "historical_snapshots.db"
            HistoricalSnapshotRepository(db_path)

            with closing(sqlite3.connect(db_path)) as connection:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    ).fetchall()
                }

        self.assertIn("financial_statement_snapshots", tables)
        self.assertIn("sap_score_snapshots", tables)
        self.assertIn("snapshot_metadata", tables)

    def test_insert_and_get_financial_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            snapshot = financial_snapshot()

            repository.insert_financial_snapshot(snapshot)
            result = repository.get_financial_snapshot(
                symbol="2330.TW",
                fiscal_year=2025,
                fiscal_quarter=1,
                snapshot_date="2025-06-30",
                statement_type="income_statement",
            )

        self.assertEqual(result, snapshot)

    def test_insert_and_get_sap_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            snapshot = sap_snapshot()

            result_status = repository.insert_sap_snapshot(snapshot)
            result = repository.get_sap_snapshot(
                symbol="2330.TW",
                fiscal_year=2025,
                fiscal_quarter=1,
                snapshot_date="2025-06-30",
            )

        self.assertEqual(result_status, "generated")
        self.assertEqual(result, snapshot)

    def test_insert_sap_snapshot_updates_existing_period(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            repository.insert_sap_snapshot(sap_snapshot(sap_score=70))

            updated_snapshot = sap_snapshot(sap_score=95)
            result_status = repository.insert_sap_snapshot(updated_snapshot)
            result = repository.get_sap_snapshot(
                symbol="2330.TW",
                fiscal_year=2025,
                fiscal_quarter=1,
                snapshot_date="2025-06-30",
            )

        self.assertEqual(result_status, "updated")
        self.assertEqual(result.sap_score, 95)

    def test_query_missing_snapshot_returns_none(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")

            result = repository.get_sap_snapshot(
                symbol="9999.TW",
                fiscal_year=2025,
                fiscal_quarter=1,
                snapshot_date="2025-06-30",
            )

        self.assertIsNone(result)

    def test_list_snapshot_dates(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot(snapshot_date="2025-06-30"))
            repository.insert_sap_snapshot(sap_snapshot(snapshot_date="2025-09-30"))

            dates = repository.list_snapshot_dates()

        self.assertEqual(dates, ["2025-06-30", "2025-09-30"])

    def test_list_symbols(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot(symbol="2330.TW"))
            repository.insert_sap_snapshot(sap_snapshot(symbol="2454.TW"))

            symbols = repository.list_symbols()

        self.assertEqual(symbols, ["2330.TW", "2454.TW"])

    def test_list_financial_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            repository.insert_financial_snapshot(financial_snapshot(symbol="2454.TW"))
            repository.insert_financial_snapshot(financial_snapshot(symbol="2330.TW"))

            snapshots = repository.list_financial_snapshots()

        self.assertEqual([snapshot.symbol for snapshot in snapshots], ["2330.TW", "2454.TW"])


def financial_snapshot(symbol="2330.TW", snapshot_date="2025-06-30"):
    return FinancialStatementSnapshot(
        symbol=symbol,
        fiscal_year=2025,
        fiscal_quarter=1,
        statement_date="2025-03-31",
        published_date="2025-05-15",
        snapshot_date=snapshot_date,
        source="fixture",
        source_version="v1",
        is_point_in_time=True,
        created_at="2026-01-01T00:00:00+00:00",
        statement_type="income_statement",
        payload_json='{"net_income": 100}',
        warning="",
    )


def sap_snapshot(symbol="2330.TW", snapshot_date="2025-06-30", sap_score=90):
    return SAPScoreSnapshot(
        symbol=symbol,
        fiscal_year=2025,
        fiscal_quarter=1,
        statement_date="2025-03-31",
        published_date="2025-05-15",
        snapshot_date=snapshot_date,
        source="fixture",
        source_version="v1",
        is_point_in_time=True,
        created_at="2026-01-01T00:00:00+00:00",
        sap_score=sap_score,
        piotroski_score=8,
        data_quality_score=100,
        credibility_grade="A",
        warning="",
    )


if __name__ == "__main__":
    unittest.main()
