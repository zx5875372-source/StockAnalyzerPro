import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from backtest.cli import build_config_from_args, parse_args


class BacktestCLITests(unittest.TestCase):
    def test_default_arguments(self):
        args = parse_args([])
        config = build_config_from_args(args)

        self.assertEqual(config.start_date, "2023-01-01")
        self.assertEqual(config.end_date, "2025-12-31")
        self.assertEqual(config.initial_cash, 1_000_000)
        self.assertEqual(config.benchmark_symbol, "0050.TW")
        self.assertEqual(Path(config.snapshot_path).as_posix(), "data/snapshots/generated_sap_scores.csv")
        self.assertEqual(config.snapshot_source, "csv")
        self.assertEqual(Path(config.snapshot_db_path).as_posix(), "historical_snapshots.db")
        self.assertEqual(Path(config.universe_path).as_posix(), "tests/sample_data/sample_stocks.json")
        self.assertEqual(config.strategy_name, "sap")

    def test_custom_benchmark(self):
        args = parse_args(["--benchmark", "006208.TW"])
        config = build_config_from_args(args)

        self.assertEqual(config.benchmark_symbol, "006208.TW")

    def test_strategy_piotroski_argument(self):
        args = parse_args(["--strategy", "piotroski"])
        config = build_config_from_args(args)

        self.assertEqual(config.strategy_name, "piotroski")

    def test_unknown_strategy_argument_is_rejected(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                parse_args(["--strategy", "missing"])

    def test_repository_snapshot_source_argument(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "historical_snapshots.db"
            db_path.write_text("", encoding="utf-8")
            args = parse_args(["--snapshot-source", "repository", "--snapshot-db", str(db_path)])

            config = build_config_from_args(args)

        self.assertEqual(config.snapshot_source, "repository")
        self.assertEqual(config.snapshot_db_path, db_path)

    def test_missing_repository_snapshot_db_has_clear_error(self):
        args = parse_args(["--snapshot-source", "repository", "--snapshot-db", "missing.db"])

        with self.assertRaisesRegex(ValueError, "snapshot repository db"):
            build_config_from_args(args)

    def test_capital_must_be_positive(self):
        args = parse_args(["--capital", "0"])

        with self.assertRaisesRegex(ValueError, "capital"):
            build_config_from_args(args)

    def test_start_must_not_be_after_end(self):
        args = parse_args(["--start", "2025-12-31", "--end", "2024-01-01"])

        with self.assertRaisesRegex(ValueError, "start"):
            build_config_from_args(args)


if __name__ == "__main__":
    unittest.main()
