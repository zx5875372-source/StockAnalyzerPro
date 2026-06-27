import argparse
import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from provider_multi_dry_run import (
    build_summary,
    parse_args,
    resolve_symbols,
    run_multi_dry_run,
)


class ProviderMultiDryRunTests(unittest.TestCase):
    def test_symbols_input(self):
        args = parse_args(["--provider", "composite", "--symbols", "2330", "2454", "2327"])

        self.assertEqual(args.symbols, ["2330", "2454", "2327"])
        self.assertEqual(resolve_symbols(args), ["2330", "2454", "2327"])

    def test_watchlist_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            watchlist_path = Path(temp_dir) / "watchlist.json"
            watchlist_path.write_text('["2330", "2454"]', encoding="utf-8")
            args = parse_args(["--source", "watchlist"])

            with patch("provider_multi_dry_run.DEFAULT_WATCHLIST_PATH", watchlist_path):
                symbols = resolve_symbols(args)

        self.assertEqual(symbols, ["2330", "2454"])

    def test_sample_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            sample_path = Path(temp_dir) / "sample_stocks.json"
            sample_path.write_text('[{"symbol": "2330"}, {"symbol": "2454"}]', encoding="utf-8")
            args = parse_args(["--source", "sample"])

            with patch("provider_multi_dry_run.DEFAULT_SAMPLE_PATH", sample_path):
                symbols = resolve_symbols(args)

        self.assertEqual(symbols, ["2330", "2454"])

    def test_markdown_summary_and_csv_generation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "provider_multi_dry_run.md"
            csv_path = Path(temp_dir) / "provider_multi_dry_run.csv"
            args = parse_args(
                [
                    "--symbols",
                    "2330",
                    "2454",
                    "--output",
                    str(output_path),
                    "--csv",
                    str(csv_path),
                ]
            )

            result = run_multi_dry_run(args, dry_run_func=successful_runner)

            markdown = output_path.read_text(encoding="utf-8")
            with csv_path.open("r", encoding="utf-8-sig") as file:
                rows = list(csv.DictReader(file))

        self.assertEqual(result["summary"]["total_count"], 2)
        self.assertIn("## Summary", markdown)
        self.assertIn("可考慮進入下一階段", markdown)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["normalized_symbol"], "2330.TW")

    def test_recommendation_logic_pass(self):
        rows = [
            row("2330.TW", selected_provider="finmind", missing_fields_count=0),
            row("2454.TW", selected_provider="finmind", missing_fields_count=0),
            row("2327.TW", selected_provider="finmind", missing_fields_count=0),
            row("AAPL", selected_provider="yahoo", missing_fields_count=0),
            row("6290.TWO", selected_provider="finmind", missing_fields_count=1),
        ]

        summary = build_summary(rows)

        self.assertTrue(summary["recommended"])
        self.assertIn("可考慮", summary["recommendation"])

    def test_recommendation_logic_fail(self):
        rows = [
            row("2330.TW", selected_provider="yahoo", fallback_used=True, missing_fields_count=2),
            row("2454.TW", selected_provider="yahoo", fallback_used=True, missing_fields_count=2),
            row("2327.TW", status="failed", error="planned failure"),
        ]

        summary = build_summary(rows)

        self.assertFalse(summary["recommended"])
        self.assertEqual(summary["recommendation"], "暫不建議切換 runtime default。")

    def test_failure_row_does_not_crash(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            args = parse_args(
                [
                    "--symbols",
                    "2330",
                    "9999",
                    "--output",
                    str(Path(temp_dir) / "out.md"),
                    "--csv",
                    str(Path(temp_dir) / "out.csv"),
                ]
            )

            result = run_multi_dry_run(args, dry_run_func=mixed_runner)

        self.assertEqual(result["summary"]["failed_count"], 1)
        self.assertEqual(result["rows"][1]["status"], "failed")
        self.assertIn("planned failure", result["rows"][1]["error"])


def successful_runner(args: argparse.Namespace):
    return dry_run_result(args.symbol)


def mixed_runner(args: argparse.Namespace):
    if args.symbol == "9999":
        return dry_run_result(args.symbol, success=False, error="planned failure")
    return dry_run_result(args.symbol)


def dry_run_result(symbol, success=True, error=None):
    normalized_symbol = f"{symbol}.TW" if str(symbol).isdigit() else str(symbol)
    return {
        "success": success,
        "symbol": symbol,
        "normalized_symbol": normalized_symbol,
        "provider": "composite",
        "selected_provider": "finmind" if success else "",
        "fallback_used": False,
        "fallback_reason": "",
        "symbol_type": "taiwan_stock",
        "source_chain": ["finmind"] if success else [],
        "mapped_fields_count": 10 if success else 0,
        "derived_fields_count": 2 if success else 0,
        "missing_fields_count": 0 if success else 0,
        "diagnostics": ["fake diagnostic"] if success else [],
        "error": error,
    }


def row(
    normalized_symbol,
    selected_provider="finmind",
    fallback_used=False,
    missing_fields_count=0,
    status="success",
    error="",
):
    return {
        "symbol": normalized_symbol,
        "normalized_symbol": normalized_symbol,
        "symbol_type": "taiwan_stock",
        "selected_provider": selected_provider,
        "fallback_used": fallback_used,
        "fallback_reason": "",
        "mapped_fields_count": 10,
        "derived_fields_count": 2,
        "missing_fields_count": missing_fields_count,
        "status": status,
        "error": error,
        "diagnostics": [],
    }


if __name__ == "__main__":
    unittest.main()
