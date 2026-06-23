import tempfile
import unittest
from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.qualification import HistoricalQualifier, format_qualification_report
from historical.repository import HistoricalSnapshotRepository
from historical_qualify import parse_args, run_qualification


class HistoricalQualificationTests(unittest.TestCase):
    def test_repository_with_all_point_in_time_sap_snapshots_can_formal_backtest(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            repository.insert_sap_snapshot(sap_snapshot(symbol="2330.TW"))
            repository.insert_sap_snapshot(sap_snapshot(symbol="2454.TW", fiscal_quarter=2))

            result = HistoricalQualifier().qualify_repository(repository)

        self.assertEqual(result.sap_snapshot_count, 2)
        self.assertEqual(result.qualified_sap_snapshot_count, 2)
        self.assertEqual(result.research_only_count, 0)
        self.assertTrue(result.can_formal_backtest)

    def test_missing_published_date_fallback_is_research_only(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")
            repository.insert_financial_snapshot(
                financial_snapshot(is_point_in_time=False, warning="missing_published_date")
            )
            repository.insert_sap_snapshot(
                sap_snapshot(is_point_in_time=False, warning="missing_published_date;not_point_in_time")
            )

            result = HistoricalQualifier().qualify_repository(repository)

        self.assertEqual(result.total_snapshots, 2)
        self.assertEqual(result.research_only_count, 2)
        self.assertEqual(result.missing_published_date_count, 2)
        self.assertEqual(result.not_point_in_time_count, 2)
        self.assertEqual(result.research_only_sap_snapshot_count, 1)
        self.assertFalse(result.can_formal_backtest)
        self.assertEqual(result.disqualification_reasons["missing_published_date"], 2)

    def test_empty_repository_report_is_clear(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repository = HistoricalSnapshotRepository(Path(temp_dir) / "historical_snapshots.db")

            result = HistoricalQualifier().qualify_repository(repository)
            report = format_qualification_report(result)

        self.assertEqual(result.total_snapshots, 0)
        self.assertFalse(result.can_formal_backtest)
        self.assertIn("| Total Snapshots | 0 |", report)
        self.assertIn("| Can Formal Backtest | false |", report)

    def test_cli_defaults(self):
        args = parse_args([])

        self.assertEqual(args.db, "historical_snapshots.db")
        self.assertEqual(Path(args.output).as_posix(), "reports/historical_qualification_report.md")

    def test_run_qualification_writes_report(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "historical_snapshots.db"
            output_path = temp_path / "historical_qualification_report.md"
            repository = HistoricalSnapshotRepository(db_path)
            repository.insert_sap_snapshot(sap_snapshot())

            result = run_qualification(db_path=db_path, output_path=output_path)
            content = output_path.read_text(encoding="utf-8")

        self.assertTrue(result.can_formal_backtest)
        self.assertIn("# Historical Qualification Report", content)
        self.assertIn("| Qualified SAP Snapshots | 1 |", content)


def financial_snapshot(is_point_in_time=True, warning=""):
    return FinancialStatementSnapshot(
        symbol="2330.TW",
        fiscal_year=2025,
        fiscal_quarter=1,
        statement_date="2025-03-31",
        published_date="2025-03-31",
        snapshot_date="2025-03-31",
        source="finmind",
        source_version="v1",
        is_point_in_time=is_point_in_time,
        created_at="2025-03-31T00:00:00+00:00",
        statement_type="income_statement",
        payload_json="{}",
        warning=warning,
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


if __name__ == "__main__":
    unittest.main()
