import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backtest.engine import BacktestConfig, BacktestEngine
from backtest.portfolio import Portfolio
from backtest.snapshot import SnapshotScoreStore
from backtest.strategy import SAPScoreStrategy
from historical.models import SAPScoreSnapshot
from historical.repository import HistoricalSnapshotRepository


class BacktestRepositorySnapshotSourceTests(unittest.TestCase):
    def test_snapshot_store_reads_sap_snapshots_from_repository(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            repository.insert_sap_snapshot(sap_snapshot(symbol="2330.TW", sap_score=90))
            repository.insert_sap_snapshot(
                sap_snapshot(symbol="2454.TW", sap_score=85, is_point_in_time=False, warning="missing_published_date")
            )

            store = SnapshotScoreStore.from_repository(repository)

        self.assertTrue(store.available())
        self.assertEqual(store.latest_before("2330", "2025-07-01")["sap_score"], 90)
        self.assertEqual(
            store.warning_counts(),
            {
                "missing_published_date": 1,
                "not_point_in_time": 1,
            },
        )

    def test_engine_loads_repository_snapshot_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "historical_snapshots.db"
            universe_path = temp_path / "universe.json"
            universe_path.write_text('[{"symbol": "2330"}]', encoding="utf-8")
            repository = HistoricalSnapshotRepository(db_path)
            repository.insert_sap_snapshot(sap_snapshot(symbol="2330.TW", sap_score=90))
            config = BacktestConfig(
                start_date="2025-01-01",
                end_date="2025-01-31",
                universe_path=universe_path,
                snapshot_source="repository",
                snapshot_db_path=db_path,
            )
            engine = BacktestEngine(
                strategy=SAPScoreStrategy(),
                portfolio=Portfolio(initial_cash=config.initial_cash),
                config=config,
                price_provider=StaticPriceProvider(),
            )

            engine.load_data()

        self.assertEqual(engine.snapshot_source, f"repository:{db_path}")
        self.assertTrue(engine.snapshots.available())
        self.assertEqual(engine.snapshots.latest_before("2330", "2025-07-01")["sap_score"], 90)


class StaticPriceProvider:
    def load_price_history(self, symbols, start_date, end_date):
        return {
            symbol: pd.Series(
                [100],
                index=pd.to_datetime(["2025-01-31"]),
            )
            for symbol in symbols
        }, []


def sap_snapshot(
    symbol="2330.TW",
    sap_score=90,
    is_point_in_time=True,
    warning="",
):
    return SAPScoreSnapshot(
        symbol=symbol,
        fiscal_year=2025,
        fiscal_quarter=1,
        statement_date="2025-03-31",
        published_date="2025-05-15",
        snapshot_date="2025-05-15",
        source="historical_sap_generator",
        source_version="v1",
        is_point_in_time=is_point_in_time,
        created_at="2025-05-15T00:00:00+00:00",
        sap_score=sap_score,
        piotroski_score=8,
        data_quality_score=95,
        credibility_grade="A",
        warning=warning,
    )


if __name__ == "__main__":
    unittest.main()
