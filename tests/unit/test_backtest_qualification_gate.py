import tempfile
import unittest
from pathlib import Path

import pandas as pd

from backtest.engine import BacktestConfig, BacktestEngine
from backtest.portfolio import Portfolio
from backtest.report import BacktestReportWriter
from backtest.snapshot import SnapshotScoreStore
from backtest.strategy import SAPScoreStrategy
from historical.models import SAPScoreSnapshot
from historical.repository import HistoricalSnapshotRepository


RESEARCH_ONLY_NOTICE = "此回測僅供研究與系統驗證，不可視為正式 point-in-time 投資績效。"


class BacktestQualificationGateTests(unittest.TestCase):
    def test_repository_snapshots_all_point_in_time_are_formal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = build_repository_engine(
                Path(temp_dir),
                [
                    sap_snapshot(symbol="2330.TW"),
                    sap_snapshot(symbol="2454.TW", fiscal_quarter=2),
                ],
            )

            engine.load_data()
            summary = engine.summary()

        self.assertEqual(summary["qualification_grade"], "A")
        self.assertEqual(summary["research_only_count"], 0)
        self.assertEqual(summary["point_in_time_count"], 2)
        self.assertEqual(summary["missing_published_date_count"], 0)
        self.assertEqual(summary["not_point_in_time_count"], 0)
        self.assertEqual(summary["qualification_notice"], "")

    def test_missing_published_date_is_research_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = build_repository_engine(
                Path(temp_dir),
                [
                    sap_snapshot(
                        is_point_in_time=False,
                        warning="missing_published_date",
                    )
                ],
            )

            engine.load_data()
            summary = engine.summary()

        self.assertEqual(summary["qualification_grade"], "C")
        self.assertEqual(summary["research_only_count"], 1)
        self.assertEqual(summary["missing_published_date_count"], 1)
        self.assertEqual(summary["not_point_in_time_count"], 1)
        self.assertEqual(summary["qualification_notice"], RESEARCH_ONLY_NOTICE)

    def test_not_point_in_time_is_research_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = build_repository_engine(
                Path(temp_dir),
                [sap_snapshot(is_point_in_time=False, warning="")],
            )

            engine.load_data()
            summary = engine.summary()

        self.assertEqual(summary["qualification_grade"], "C")
        self.assertEqual(summary["research_only_count"], 1)
        self.assertEqual(summary["missing_published_date_count"], 0)
        self.assertEqual(summary["not_point_in_time_count"], 1)

    def test_csv_snapshot_source_keeps_legacy_credibility(self):
        engine = BacktestEngine(
            strategy=SAPScoreStrategy(),
            portfolio=Portfolio(initial_cash=1_000_000),
            config=BacktestConfig(snapshot_source="csv"),
            price_provider=StaticPriceProvider(),
        )
        engine.snapshots = SnapshotScoreStore(
            [
                {
                    "date": pd.Timestamp("2024-12-31"),
                    "symbol": "2330.TW",
                    "sap_score": 90,
                    "piotroski_score": 8,
                    "data_quality_score": 95,
                    "warning": "not_point_in_time",
                }
            ]
        )
        engine.price_history = {"2330.TW": pd.Series([100], index=pd.to_datetime(["2025-01-31"]))}
        engine.look_ahead_safe = True

        summary = engine.summary()

        self.assertEqual(summary["qualification_grade"], "N/A")
        self.assertEqual(summary["qualification_reason"], "CSV snapshot source uses existing credibility logic.")
        self.assertEqual(summary["snapshot_warning_counts"], {"not_point_in_time": 1})
        self.assertEqual(summary["credibility_grade"], "D")

    def test_markdown_report_displays_research_only_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            summary_path = Path(temp_dir) / "backtest_summary.md"
            equity_path = Path(temp_dir) / "backtest_equity_curve.csv"
            writer = BacktestReportWriter(summary_path=summary_path, equity_curve_path=equity_path)

            writer.write_markdown(sample_result())
            content = summary_path.read_text(encoding="utf-8")

        self.assertIn("## Historical Qualification", content)
        self.assertIn("| Qualification Grade | C |", content)
        self.assertIn("| Research-only Count | 1 |", content)
        self.assertIn(RESEARCH_ONLY_NOTICE, content)


class StaticPriceProvider:
    def load_price_history(self, symbols, start_date, end_date):
        return {
            symbol: pd.Series(
                [100],
                index=pd.to_datetime(["2025-01-31"]),
            )
            for symbol in symbols
        }, []


def build_repository_engine(temp_path: Path, snapshots: list[SAPScoreSnapshot]) -> BacktestEngine:
    db_path = temp_path / "historical_snapshots.db"
    universe_path = temp_path / "universe.json"
    universe_path.write_text('[{"symbol": "2330"}]', encoding="utf-8")
    repository = HistoricalSnapshotRepository(db_path)
    for snapshot in snapshots:
        repository.insert_sap_snapshot(snapshot)

    config = BacktestConfig(
        start_date="2025-01-01",
        end_date="2025-01-31",
        universe_path=universe_path,
        snapshot_source="repository",
        snapshot_db_path=db_path,
    )
    return BacktestEngine(
        strategy=SAPScoreStrategy(),
        portfolio=Portfolio(initial_cash=config.initial_cash),
        config=config,
        price_provider=StaticPriceProvider(),
    )


def sap_snapshot(
    symbol="2330.TW",
    fiscal_quarter=1,
    is_point_in_time=True,
    warning="",
):
    return SAPScoreSnapshot(
        symbol=symbol,
        fiscal_year=2025,
        fiscal_quarter=fiscal_quarter,
        statement_date="2025-03-31",
        published_date="2025-05-15",
        snapshot_date="2025-05-15",
        source="historical_sap_generator",
        source_version="v1",
        is_point_in_time=is_point_in_time,
        created_at="2025-05-15T00:00:00+00:00",
        sap_score=90,
        piotroski_score=8,
        data_quality_score=95,
        credibility_grade="A",
        warning=warning,
    )


def sample_result():
    return {
        "metrics": {
            "total_return": 0.1,
            "cagr": 0.1,
            "max_drawdown": -0.05,
            "win_rate": 0.5,
            "benchmark_total_return": 0.08,
            "benchmark_cagr": 0.08,
            "excess_return": 0.02,
            "excess_cagr": 0.02,
            "strategy_vs_benchmark": "outperform",
        },
        "config": {
            "start_date": "2025-01-01",
            "end_date": "2025-01-31",
            "initial_cash": 1_000_000,
            "benchmark_symbol": "0050.TW",
            "universe_path": "tests/sample_data/sample_stocks.json",
            "min_sap_score": 80,
            "min_piotroski_score": 7,
            "min_data_quality_score": 80,
        },
        "strategy_name": "sap",
        "snapshot_source": "repository:test.db",
        "look_ahead_safe": True,
        "snapshot_point_in_time": False,
        "credibility_grade": "C",
        "credibility_reason": "snapshot warning",
        "credibility_notice": "",
        "qualification_grade": "C",
        "qualification_reason": "Repository contains research-only snapshots.",
        "qualification_notice": RESEARCH_ONLY_NOTICE,
        "research_only_count": 1,
        "point_in_time_count": 0,
        "missing_published_date_count": 1,
        "not_point_in_time_count": 1,
        "selected_stock_count": 0,
        "skipped_stock_count": 0,
        "selected_symbols": [],
        "skipped_reasons": {},
        "snapshot_warning_counts": {"missing_published_date": 1},
        "diagnostics": [],
        "equity_curve": [],
    }


if __name__ == "__main__":
    unittest.main()
