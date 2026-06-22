from contextlib import redirect_stderr
from io import StringIO
import tempfile
import unittest
from pathlib import Path

from finmind_import import parse_args, resolve_token, run_import
from importers.import_result import ImportResult


class MockFinMindImporter:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def import_financial_statements(
        self,
        symbol,
        start_date=None,
        end_date=None,
        repository=None,
    ):
        self.calls.append(
            {
                "symbol": symbol,
                "start_date": start_date,
                "end_date": end_date,
                "repository": repository,
            }
        )
        return self.result


class FinMindImportCliTests(unittest.TestCase):
    def test_parse_args(self):
        args = parse_args(
            [
                "--symbol",
                "2330",
                "--start",
                "2025-01-01",
                "--end",
                "2025-12-31",
                "--db",
                "custom.db",
                "--token",
                "cli-token",
            ]
        )

        self.assertEqual(args.symbol, "2330")
        self.assertEqual(args.start_date, "2025-01-01")
        self.assertEqual(args.end_date, "2025-12-31")
        self.assertEqual(args.db, "custom.db")
        self.assertEqual(args.token, "cli-token")

    def test_token_from_env(self):
        self.assertEqual(resolve_token(None, {"FINMIND_TOKEN": "env-token"}), "env-token")
        self.assertEqual(resolve_token("cli-token", {"FINMIND_TOKEN": "env-token"}), "cli-token")
        self.assertIsNone(resolve_token(None, {}))

    def test_missing_symbol_has_clear_argparse_error(self):
        stderr = StringIO()

        with self.assertRaises(SystemExit) as error_context:
            with redirect_stderr(stderr):
                parse_args([])

        self.assertNotEqual(error_context.exception.code, 0)
        self.assertIn("--symbol", stderr.getvalue())

    def test_mock_importer_success_writes_summary(self):
        importer = MockFinMindImporter(
            ImportResult(
                importer="finmind",
                importer_version="test",
                source="finmind:2330",
                imported_count=1,
                failed_count=0,
                warnings=["row 2: duplicate warning"],
            )
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            db_path = temp_path / "historical_snapshots.db"
            summary_path = temp_path / "finmind_import_summary.md"

            summary = run_import(
                symbol="2330",
                start_date="2025-01-01",
                end_date="2025-12-31",
                db_path=db_path,
                token="test-token",
                summary_path=summary_path,
                importer=importer,
            )
            content = summary_path.read_text(encoding="utf-8")

        self.assertEqual(summary.symbol, "2330")
        self.assertEqual(summary.imported_count, 1)
        self.assertEqual(summary.failed_count, 0)
        self.assertEqual(summary.warning_count, 1)
        self.assertEqual(importer.calls[0]["symbol"], "2330")
        self.assertEqual(importer.calls[0]["start_date"], "2025-01-01")
        self.assertEqual(importer.calls[0]["end_date"], "2025-12-31")
        self.assertIsNotNone(importer.calls[0]["repository"])
        self.assertIn("# FinMind Import Summary", content)
        self.assertIn("| Symbol | 2330 |", content)
        self.assertIn("| Repository Database |", content)
        self.assertIn("- row 2: duplicate warning", content)


if __name__ == "__main__":
    unittest.main()
