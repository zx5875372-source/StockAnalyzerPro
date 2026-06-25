import argparse
import unittest

from data_provider import ProviderError
from provider_dry_run import (
    build_mock_composite_provider,
    format_result,
    parse_args,
    run_dry_run,
)


class ProviderDryRunTests(unittest.TestCase):
    def test_parse_cli_args(self):
        args = parse_args(
            [
                "--provider",
                "composite",
                "--symbol",
                "2330",
                "--start",
                "2022-01-01",
                "--end",
                "2024-12-31",
                "--mock",
                "--show-diagnostics",
            ]
        )

        self.assertEqual(args.provider, "composite")
        self.assertEqual(args.symbol, "2330")
        self.assertEqual(args.start, "2022-01-01")
        self.assertEqual(args.end, "2024-12-31")
        self.assertTrue(args.mock)
        self.assertTrue(args.show_diagnostics)

    def test_composite_mock_taiwan_stock_routes_to_finmind(self):
        args = argparse.Namespace(provider="composite", symbol="2330", mock=True, show_diagnostics=False)

        result = run_dry_run(args)

        self.assertTrue(result["success"])
        self.assertEqual(result["normalized_symbol"], "2330.TW")
        self.assertEqual(result["selected_provider"], "finmind")
        self.assertFalse(result["fallback_used"])
        self.assertEqual(result["symbol_type"], "taiwan_stock")
        self.assertEqual(result["source_chain"], ["finmind"])
        self.assertEqual(result["mapped_fields_count"], 10)
        self.assertEqual(result["derived_fields_count"], 2)

    def test_composite_mock_fallback_routes_to_yahoo(self):
        provider = build_mock_composite_provider(
            finmind_failure=ProviderError("FinMind API error for TaiwanStockFinancialStatements: HTTP 400")
        )
        args = argparse.Namespace(provider="composite", symbol="2330", mock=True, show_diagnostics=False)

        result = run_dry_run(args, provider=provider)

        self.assertTrue(result["success"])
        self.assertEqual(result["selected_provider"], "yahoo")
        self.assertTrue(result["fallback_used"])
        self.assertIn("FinMind API error", result["fallback_reason"])
        self.assertEqual(result["source_chain"], ["finmind", "yahoo"])

    def test_composite_api_error_diagnostics_show_fallback_used_true(self):
        provider = build_mock_composite_provider(
            finmind_failure=ProviderError("FinMind API error for TaiwanStockFinancialStatements: HTTP 400")
        )
        args = argparse.Namespace(provider="composite", symbol="2330", mock=True, show_diagnostics=True)

        result = run_dry_run(args, provider=provider)
        output = format_result(result, show_diagnostics=True)

        self.assertTrue(result["fallback_used"])
        self.assertIn("selected_provider: yahoo", output)
        self.assertIn("fallback_used: true", output)
        self.assertIn("FinMind API error", output)
        self.assertIn("source_chain: finmind -> yahoo", output)

    def test_composite_mock_non_taiwan_routes_to_yahoo(self):
        args = argparse.Namespace(provider="composite", symbol="AAPL", mock=True, show_diagnostics=False)

        result = run_dry_run(args)

        self.assertTrue(result["success"])
        self.assertEqual(result["normalized_symbol"], "AAPL")
        self.assertEqual(result["selected_provider"], "yahoo")
        self.assertFalse(result["fallback_used"])
        self.assertEqual(result["symbol_type"], "non_taiwan")
        self.assertEqual(result["source_chain"], ["yahoo"])

    def test_show_diagnostics_formats_diagnostics(self):
        args = argparse.Namespace(provider="composite", symbol="2330", mock=True, show_diagnostics=True)
        result = run_dry_run(args)

        output = format_result(result, show_diagnostics=True)

        self.assertIn("diagnostics:", output)
        self.assertIn("mock financial data", output)
        self.assertIn("mapped_fields_count: 10", output)
        self.assertIn("derived_fields_count: 2", output)
        self.assertIn("selected_provider: finmind", output)

    def test_failure_does_not_crash(self):
        args = argparse.Namespace(provider="finmind", symbol="AAPL", mock=True, show_diagnostics=False)

        result = run_dry_run(args)

        self.assertFalse(result["success"])
        self.assertEqual(result["provider"], "finmind")
        self.assertEqual(result["normalized_symbol"], "AAPL")
        self.assertIn("mock financial data not found", result["error"])


if __name__ == "__main__":
    unittest.main()
