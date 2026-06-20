import unittest
from unittest.mock import patch

from models.financial_data import FinancialData, FinancialPeriod
from modules.downloader import get_stock_data


class DownloaderProviderIntegrationTests(unittest.TestCase):
    def test_get_stock_data_uses_provider_factory_yahoo_provider(self):
        expected_data = FinancialData(
            symbol="2330.TW",
            company_name="Factory Company",
            current=FinancialPeriod(period="2025-12-31", net_income=100),
        )
        provider = FakeProvider(expected_data)
        factory = FakeFactory(provider)

        with patch("modules.downloader.ProviderFactory.with_defaults", return_value=factory):
            result = get_stock_data("2330")

        self.assertIs(result, expected_data)
        self.assertEqual(factory.created_provider_names, ["yahoo"])
        self.assertEqual(provider.requested_symbols, ["2330"])


class FakeFactory:
    def __init__(self, provider):
        self.provider = provider
        self.created_provider_names = []

    def create(self, name):
        self.created_provider_names.append(name)
        return self.provider


class FakeProvider:
    def __init__(self, financial_data):
        self.financial_data = financial_data
        self.requested_symbols = []

    def get_financial_data(self, symbol, as_of=None):
        self.requested_symbols.append(symbol)
        return self.financial_data


if __name__ == "__main__":
    unittest.main()
