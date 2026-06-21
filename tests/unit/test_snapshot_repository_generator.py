import tempfile
import unittest
from pathlib import Path

from historical.generator import (
    NOT_POINT_IN_TIME_WARNING,
    SnapshotGenerator,
    build_sap_score_snapshot,
)
from historical.repository import HistoricalSnapshotRepository


class SnapshotRepositoryGeneratorTests(unittest.TestCase):
    def test_generator_creates_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            generator = SnapshotGenerator(repository, scan_func=fake_scan_stock)

            result = generator.generate(
                [{"symbol": "2330", "name": "台積電", "category": "半導體"}],
                snapshot_date="2026-06-21",
                verbose=False,
            )

        self.assertEqual(result.total_count, 1)
        self.assertEqual(result.inserted_count, 1)
        self.assertEqual(result.failed_count, 0)
        self.assertEqual(result.snapshots[0].symbol, "2330.TW")

    def test_warning_is_not_point_in_time(self):
        snapshot = build_sap_score_snapshot(
            stock={"symbol": "2330"},
            analysis=fake_scan_stock({"symbol": "2330"}),
            snapshot_date="2026-06-21",
            created_at="2026-06-21T00:00:00+00:00",
        )

        self.assertEqual(snapshot.warning, NOT_POINT_IN_TIME_WARNING)
        self.assertFalse(snapshot.is_point_in_time)
        self.assertEqual(snapshot.source, "current_analysis_proxy")
        self.assertEqual(snapshot.source_version, "v0")

    def test_repository_can_query_written_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            generator = SnapshotGenerator(repository, scan_func=fake_scan_stock)

            generator.generate(
                [{"symbol": "2330", "name": "台積電", "category": "半導體"}],
                snapshot_date="2026-06-21",
                verbose=False,
            )
            snapshot = repository.get_sap_snapshot(
                symbol="2330.TW",
                fiscal_year=2026,
                fiscal_quarter=2,
                snapshot_date="2026-06-21",
            )

        self.assertIsNotNone(snapshot)
        self.assertEqual(snapshot.symbol, "2330.TW")
        self.assertEqual(snapshot.warning, NOT_POINT_IN_TIME_WARNING)
        self.assertEqual(snapshot.sap_score, 90)
        self.assertEqual(snapshot.piotroski_score, 8)
        self.assertEqual(snapshot.data_quality_score, 100)


def fake_scan_stock(stock):
    return {
        "symbol": "2330.TW",
        "status": "success",
        "sap_score": 90,
        "piotroski_score": 8,
        "data_quality_score": 100,
    }


if __name__ == "__main__":
    unittest.main()
