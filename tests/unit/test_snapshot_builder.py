import csv
import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backtest.engine import BacktestConfig, BacktestEngine
from backtest.portfolio import Portfolio
from backtest.strategy import SAPScoreStrategy
from snapshot_builder import SNAPSHOT_FIELDNAMES, build_snapshot_rows, write_snapshot


class SnapshotBuilderTests(unittest.TestCase):
    def test_snapshot_builder_outputs_expected_columns(self):
        stocks = [{"symbol": "2330", "name": "台積電", "category": "半導體"}]
        rows = build_snapshot_rows(stocks, ["2023-03-31"], scan_func=fake_scan_stock, verbose=False)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "generated_sap_scores.csv"
            write_snapshot(rows, output_path)

            with output_path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames
                loaded_rows = list(reader)

        self.assertEqual(fieldnames, SNAPSHOT_FIELDNAMES)
        self.assertEqual(len(loaded_rows), 1)

    def test_snapshot_builder_marks_proxy_warning(self):
        stocks = [{"symbol": "2330", "name": "台積電", "category": "半導體"}]
        rows = build_snapshot_rows(stocks, ["2023-03-31"], scan_func=fake_scan_stock, verbose=False)

        self.assertEqual(rows[0]["source"], "current_analysis_proxy")
        self.assertEqual(rows[0]["warning"], "not_point_in_time")

    def test_backtest_reads_generated_snapshot(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            universe_path = temp_path / "sample_stocks.json"
            snapshot_path = temp_path / "generated_sap_scores.csv"
            universe_path.write_text(
                json.dumps([{"symbol": "2330", "name": "台積電", "category": "半導體"}]),
                encoding="utf-8",
            )
            write_snapshot(
                [
                    {
                        "date": "2023-03-31",
                        "symbol": "2330.TW",
                        "sap_score": 90,
                        "piotroski_score": 8,
                        "data_quality_score": 100,
                        "source": "current_analysis_proxy",
                        "warning": "not_point_in_time",
                    }
                ],
                snapshot_path,
            )

            config = BacktestConfig(
                start_date="2023-03-01",
                end_date="2023-04-30",
                universe_path=universe_path,
                snapshot_path=snapshot_path,
            )
            engine = BacktestEngine(
                strategy=SAPScoreStrategy(),
                portfolio=Portfolio(initial_cash=config.initial_cash),
                config=config,
                price_provider=FakePriceProvider(),
            )

            result = engine.run()

        self.assertEqual(result["snapshot_source"], str(snapshot_path))
        self.assertEqual(result["selected_symbols"], ["2330.TW"])
        self.assertEqual(result["snapshot_warning_counts"], {"not_point_in_time": 1})
        self.assertTrue(result["look_ahead_safe"])
        self.assertFalse(result["snapshot_point_in_time"])
        self.assertEqual(result["metrics"]["strategy_vs_benchmark"], "benchmark unavailable")
        self.assertIn("benchmark unavailable: 0050.TW", result["diagnostics"])


def fake_scan_stock(stock):
    return {
        "symbol": "2330.TW",
        "status": "success",
        "sap_score": 90,
        "piotroski_score": 8,
        "data_quality_score": 100,
    }


class FakePriceProvider:
    def load_price_history(self, symbols, start_date, end_date):
        return {
            "2330.TW": pd.Series(
                [500, 550],
                index=pd.to_datetime(["2023-03-31", "2023-04-28"]),
            )
        }, []


if __name__ == "__main__":
    unittest.main()
