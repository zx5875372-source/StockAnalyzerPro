import json
import tempfile
import unittest
from pathlib import Path

from historical.models import FinancialStatementSnapshot
from historical.repository import HistoricalSnapshotRepository
from historical_generate_sap import parse_args, run_generate


class HistoricalGenerateSAPCliTests(unittest.TestCase):
    def test_cli_default_args(self):
        args = parse_args([])

        self.assertEqual(args.db, "historical_snapshots.db")
        self.assertIsNone(args.symbol)
        self.assertIsNone(args.year)
        self.assertIsNone(args.quarter)

    def test_filter_symbol(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = seed_repository(temp_path)
            summary = run_generate(
                db_path=repository.db_path,
                symbol="2330",
                summary_path=temp_path / "historical_generator_summary.md",
            )
            generated = repository.get_sap_snapshot("2330.TW", 2025, 1, "2025-06-30")
            skipped = repository.get_sap_snapshot("2454.TW", 2025, 2, "2025-09-30")

        self.assertEqual(summary.generated, 1)
        self.assertEqual(summary.filters["symbol"], "2330.TW")
        self.assertIsNotNone(generated)
        self.assertIsNone(skipped)

    def test_filter_year_and_quarter(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = seed_repository(temp_path)
            summary = run_generate(
                db_path=repository.db_path,
                year=2025,
                quarter=2,
                summary_path=temp_path / "historical_generator_summary.md",
            )
            generated = repository.get_sap_snapshot("2454.TW", 2025, 2, "2025-09-30")
            skipped = repository.get_sap_snapshot("2330.TW", 2025, 1, "2025-06-30")

        self.assertEqual(summary.generated, 1)
        self.assertEqual(summary.filters["year"], 2025)
        self.assertEqual(summary.filters["quarter"], 2)
        self.assertIsNotNone(generated)
        self.assertIsNone(skipped)

    def test_summary_report_is_generated(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = seed_repository(temp_path)
            summary_path = temp_path / "historical_generator_summary.md"

            summary = run_generate(
                db_path=repository.db_path,
                symbol="2330",
                year=2025,
                quarter=1,
                summary_path=summary_path,
            )
            content = summary_path.read_text(encoding="utf-8")

        self.assertEqual(summary.generated, 1)
        self.assertIn("# Historical Generator Summary", content)
        self.assertIn("| Database |", content)
        self.assertIn("| Generated | 1 |", content)
        self.assertIn("| Symbol | 2330.TW |", content)
        self.assertIn("| Year | 2025 |", content)
        self.assertIn("| Quarter | 1 |", content)

    def test_repository_contains_generated_sap_snapshots(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repository = seed_repository(temp_path)

            summary = run_generate(
                db_path=repository.db_path,
                summary_path=temp_path / "historical_generator_summary.md",
            )
            first = repository.get_sap_snapshot("2330.TW", 2025, 1, "2025-06-30")
            second = repository.get_sap_snapshot("2454.TW", 2025, 2, "2025-09-30")

        self.assertEqual(summary.generated, 2)
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        self.assertEqual(first.sap_score, 100)
        self.assertEqual(second.sap_score, 100)


def seed_repository(temp_path: Path) -> HistoricalSnapshotRepository:
    repository = HistoricalSnapshotRepository(temp_path / "historical_snapshots.db")
    repository.insert_financial_snapshot(
        financial_snapshot(symbol="2330.TW", fiscal_quarter=1, snapshot_date="2025-06-30")
    )
    repository.insert_financial_snapshot(
        financial_snapshot(symbol="2454.TW", fiscal_quarter=2, snapshot_date="2025-09-30")
    )
    return repository


def financial_snapshot(symbol: str, fiscal_quarter: int, snapshot_date: str):
    statement_date = "2025-03-31" if fiscal_quarter == 1 else "2025-06-30"
    published_date = "2025-05-15" if fiscal_quarter == 1 else "2025-08-15"
    return FinancialStatementSnapshot(
        symbol=symbol,
        fiscal_year=2025,
        fiscal_quarter=fiscal_quarter,
        statement_date=statement_date,
        published_date=published_date,
        snapshot_date=snapshot_date,
        source="fixture",
        source_version="v1",
        is_point_in_time=True,
        created_at="2026-01-01T00:00:00+00:00",
        statement_type="income_statement",
        payload_json=json.dumps(sample_payload()),
        warning="",
    )


def sample_payload():
    return {
        "price": 100,
        "pe": 10,
        "pb": 1.5,
        "current": {
            "net_income": 120,
            "total_assets": 1000,
            "total_equity": 500,
            "total_debt": 100,
            "long_term_debt": 100,
            "current_assets": 300,
            "current_liabilities": 100,
            "revenue": 1200,
            "gross_profit": 600,
            "operating_income": 200,
            "operating_cashflow": 150,
            "free_cashflow": 80,
            "shares_outstanding": 10,
            "eps": 12,
            "book_value_per_share": 50,
        },
        "previous": {
            "net_income": 80,
            "total_assets": 900,
            "total_equity": 450,
            "total_debt": 120,
            "long_term_debt": 120,
            "current_assets": 200,
            "current_liabilities": 100,
            "revenue": 1000,
            "gross_profit": 450,
            "operating_income": 150,
            "operating_cashflow": 90,
            "free_cashflow": 40,
            "shares_outstanding": 11,
            "eps": 8,
            "book_value_per_share": 45,
        },
    }


if __name__ == "__main__":
    unittest.main()
