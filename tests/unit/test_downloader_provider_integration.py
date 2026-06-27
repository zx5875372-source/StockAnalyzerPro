import unittest
from unittest.mock import patch

from models.financial_data import FinancialData, FinancialPeriod
from modules.downloader import get_stock_data


class DownloaderProviderIntegrationTests(unittest.TestCase):
    def test_default_provider_is_composite(self):
        provider = FakeProvider(financial_data())
        factory = FakeFactory(provider)

        with patch.dict("os.environ", {}, clear=True):
            with patch("modules.downloader.ProviderFactory.with_defaults", return_value=factory):
                result = get_stock_data("2330")

        self.assertIs(result, provider.financial_data)
        self.assertEqual(factory.created_provider_names, ["composite"])
        self.assertEqual(provider.requested_symbols, ["2330"])
        self.assertIn("provider_source: FinMind", result.diagnostics)

    def test_sap_provider_env_can_fallback_to_cached_yahoo(self):
        provider = FakeProvider(financial_data(), route=None)
        factory = FakeFactory(provider)

        with patch.dict("os.environ", {"SAP_PROVIDER": "cached_yahoo"}, clear=True):
            with patch("modules.downloader.ProviderFactory.with_defaults", return_value=factory):
                result = get_stock_data("2330")

        self.assertIs(result, provider.financial_data)
        self.assertEqual(factory.created_provider_names, ["cached_yahoo"])
        self.assertIn("provider_source: Yahoo Finance", result.diagnostics)
        self.assertIn("provider_selected_provider: yahoo", result.diagnostics)

    def test_composite_fallback_metadata_is_attached(self):
        provider = FakeProvider(
            financial_data(),
            route={
                "primary_provider": "finmind",
                "fallback_provider": "yahoo",
                "selected_provider": "yahoo",
                "fallback_used": True,
                "fallback_reason": "FinMind API error",
                "symbol_type": "taiwan_stock",
                "source_chain": ["finmind", "yahoo"],
            },
        )
        factory = FakeFactory(provider)

        with patch.dict("os.environ", {}, clear=True):
            with patch("modules.downloader.ProviderFactory.with_defaults", return_value=factory):
                result = get_stock_data("2330")

        self.assertIn("provider_source: Yahoo Finance（FinMind fallback）", result.diagnostics)
        self.assertIn("provider_fallback_used: true", result.diagnostics)
        self.assertIn("provider_fallback_reason: FinMind API error", result.diagnostics)

    def test_non_taiwan_composite_metadata_routes_to_yahoo(self):
        provider = FakeProvider(
            financial_data(symbol="AAPL"),
            route={
                "primary_provider": "finmind",
                "fallback_provider": "yahoo",
                "selected_provider": "yahoo",
                "fallback_used": False,
                "fallback_reason": None,
                "symbol_type": "non_taiwan",
                "source_chain": ["yahoo"],
            },
        )
        factory = FakeFactory(provider)

        with patch.dict("os.environ", {}, clear=True):
            with patch("modules.downloader.ProviderFactory.with_defaults", return_value=factory):
                result = get_stock_data("AAPL")

        self.assertIn("provider_source: Yahoo Finance", result.diagnostics)
        self.assertIn("provider_fallback_used: false", result.diagnostics)


class FakeFactory:
    def __init__(self, provider):
        self.provider = provider
        self.created_provider_names = []

    def create(self, name):
        self.created_provider_names.append(name)
        return self.provider


class FakeProvider:
    def __init__(self, financial_data, route="default"):
        self.financial_data = financial_data
        self.requested_symbols = []
        self.route = route

    def get_financial_data(self, symbol, as_of=None):
        self.requested_symbols.append(symbol)
        return self.financial_data

    def routing_diagnostics(self):
        if self.route == "default":
            return [
                {
                    "primary_provider": "finmind",
                    "fallback_provider": "yahoo",
                    "selected_provider": "finmind",
                    "fallback_used": False,
                    "fallback_reason": None,
                    "symbol_type": "taiwan_stock",
                    "source_chain": ["finmind"],
                }
            ]
        if self.route is None:
            return []
        return [self.route]


def financial_data(symbol="2330.TW"):
    return FinancialData(
        symbol=symbol,
        company_name="Factory Company",
        current=FinancialPeriod(period="2025-12-31", net_income=100),
    )


if __name__ == "__main__":
    unittest.main()
