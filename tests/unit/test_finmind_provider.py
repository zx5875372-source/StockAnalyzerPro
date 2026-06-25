import unittest

from data_provider import CachedDataProvider, ProviderError, create_provider
from data_provider.providers.finmind_provider import FinMindProvider
from models.financial_data import FinancialData, FinancialPeriod


class FinMindProviderTests(unittest.TestCase):
    def test_factory_creates_finmind_provider(self):
        provider = create_provider("finmind")

        self.assertIsInstance(provider, FinMindProvider)

    def test_metadata_and_initial_diagnostics(self):
        provider = FinMindProvider(client=FakeFinMindClient())

        self.assertEqual(provider.name, "finmind")
        self.assertEqual(provider.version, "skeleton-v1")
        self.assertEqual(provider.diagnostics(), [])
        self.assertEqual(provider.get_provider_diagnostics(), [])

    def test_accepts_mock_client_injection(self):
        expected = FinancialData(
            symbol="2330.TW",
            company_name="台積電",
            current=FinancialPeriod(period="2025-12-31", net_income=100),
        )
        client = FakeFinMindClient(financial_data=expected)
        provider = FinMindProvider(client=client)

        result = provider.get_financial_data("2330")

        self.assertIs(result, expected)
        self.assertEqual(client.requested_symbols, ["2330.TW"])

    def test_non_taiwan_symbol_has_clear_unsupported_diagnostic(self):
        provider = FinMindProvider(client=FakeFinMindClient())

        with self.assertRaisesRegex(ProviderError, "supports Taiwan stock symbols only"):
            provider.get_financial_data("AAPL")

        diagnostics = provider.diagnostics()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].provider, "finmind")
        self.assertEqual(diagnostics[0].severity, "warning")
        self.assertEqual(diagnostics[0].symbol, "AAPL")
        self.assertIn("Yahoo fallback", diagnostics[0].message)

    def test_mapping_placeholder_has_clear_diagnostic(self):
        provider = FinMindProvider(client=object())

        with self.assertRaisesRegex(ProviderError, "FinancialData mapping is not implemented yet"):
            provider.get_financial_data("2330")

        diagnostics = provider.get_provider_diagnostics()
        self.assertEqual(diagnostics[0].symbol, "2330.TW")
        self.assertIn("use Yahoo fallback", diagnostics[0].message)

    def test_symbol_helpers(self):
        self.assertEqual(FinMindProvider.normalize_symbol("2330"), "2330.TW")
        self.assertTrue(FinMindProvider.is_taiwan_symbol("6290.TWO"))
        self.assertFalse(FinMindProvider.is_taiwan_symbol("AAPL"))
        self.assertEqual(FinMindProvider.finmind_stock_id("2330.TW"), "2330")

    def test_cached_yahoo_default_provider_is_unchanged(self):
        provider = create_provider("cached_yahoo")

        self.assertIsInstance(provider, CachedDataProvider)


class FakeFinMindClient:
    def __init__(self, financial_data: FinancialData | None = None):
        self.financial_data = financial_data
        self.requested_symbols = []

    def get_financial_data(self, symbol: str, as_of=None):
        self.requested_symbols.append(symbol)
        if self.financial_data is None:
            raise ProviderError("mock client has no financial data")
        return self.financial_data


if __name__ == "__main__":
    unittest.main()
