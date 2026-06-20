import csv
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data_provider import CSVProvider, MockProvider, ProviderError, YahooFinanceProvider, create_provider
from data_provider.interfaces import PriceHistory
from data_provider.provider_factory import ProviderFactory
from models.financial_data import FinancialData, FinancialPeriod


class MockProviderTests(unittest.TestCase):
    def test_mock_provider_returns_injected_financial_data(self):
        financial_data = FinancialData(
            symbol="2330.TW",
            company_name="TSMC",
            current=FinancialPeriod(period="2025-12-31", net_income=100),
        )
        provider = MockProvider(financial_data={"2330.TW": financial_data})

        result = provider.get_financial_data("2330")

        self.assertEqual(result.symbol, "2330.TW")
        self.assertEqual(result.company_name, "TSMC")

    def test_mock_provider_returns_price_history_copy(self):
        frame = pd.DataFrame({"Close": [100, 110]}, index=pd.to_datetime(["2025-01-01", "2025-01-02"]))
        provider = MockProvider(price_history={"2330.TW": frame})

        result = provider.get_price_history("2330", "2025-01-01", "2025-01-31")

        self.assertIsInstance(result, PriceHistory)
        self.assertEqual(result.symbol, "2330.TW")
        self.assertEqual(result.start, "2025-01-01")
        self.assertEqual(result.end, "2025-01-31")
        pd.testing.assert_frame_equal(result.data, frame)
        self.assertIsNot(result.data, frame)

    def test_mock_provider_can_simulate_failures(self):
        provider = MockProvider(failures={"financial:2330.TW": ProviderError("planned failure")})

        with self.assertRaisesRegex(ProviderError, "planned failure"):
            provider.get_financial_data("2330")


class CSVProviderTests(unittest.TestCase):
    def test_csv_provider_reads_snapshot_csv_and_normalizes_symbols(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "snapshot.csv"
            with snapshot_path.open("w", encoding="utf-8", newline="") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=[
                        "date",
                        "symbol",
                        "sap_score",
                        "piotroski_score",
                        "data_quality_score",
                        "source",
                        "warning",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "date": "2025-12-31",
                        "symbol": "2330",
                        "sap_score": "90",
                        "piotroski_score": "8",
                        "data_quality_score": "100",
                        "source": "fixture",
                        "warning": "",
                    }
                )

            rows = CSVProvider().read_snapshot(snapshot_path)

        self.assertEqual(rows[0]["symbol"], "2330.TW")
        self.assertEqual(rows[0]["sap_score"], "90")

    def test_csv_provider_rejects_snapshot_missing_required_columns(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "snapshot.csv"
            snapshot_path.write_text("date,symbol\n2025-12-31,2330\n", encoding="utf-8")

            with self.assertRaisesRegex(ProviderError, "missing required columns"):
                CSVProvider().read_snapshot(snapshot_path)


class ProviderFactoryTests(unittest.TestCase):
    def test_default_factory_creates_supported_providers(self):
        self.assertIsInstance(create_provider("mock"), MockProvider)
        self.assertIsInstance(create_provider("csv"), CSVProvider)
        self.assertIsInstance(create_provider("yfinance"), YahooFinanceProvider)

    def test_factory_supports_custom_registration(self):
        factory = ProviderFactory()
        factory.register("custom-mock", lambda: MockProvider())

        provider = factory.create("custom_mock")

        self.assertIsInstance(provider, MockProvider)

    def test_factory_rejects_unknown_provider(self):
        with self.assertRaisesRegex(ProviderError, "Unknown provider"):
            create_provider("missing")


class YahooFinanceProviderTests(unittest.TestCase):
    def test_yahoo_provider_adapts_ticker_data_without_network(self):
        provider = YahooFinanceProvider(ticker_factory=lambda symbol: FakeTicker(symbol))

        self.assertEqual(provider.get_info("2330")["longName"], "Fake Company")
        self.assertEqual(provider.get_financials("2330").loc["Net Income"].iloc[0], 120)
        self.assertEqual(provider.get_balance_sheet("2330").loc["Total Assets"].iloc[0], 1000)
        self.assertEqual(provider.get_cashflow("2330").loc["Free Cash Flow"].iloc[0], 80)
        self.assertEqual(provider.get_history("2330", period="1mo").iloc[0]["Close"], 100)

    def test_yahoo_provider_builds_financial_data_from_ticker(self):
        provider = YahooFinanceProvider(ticker_factory=lambda symbol: FakeTicker(symbol))

        data = provider.get_financial_data("2330")

        self.assertEqual(data.symbol, "2330.TW")
        self.assertEqual(data.company_name, "Fake Company")
        self.assertEqual(data.current.net_income, 120)
        self.assertEqual(data.previous.net_income, 100)


class FakeTicker:
    def __init__(self, symbol):
        self.symbol = symbol
        self.info = {
            "longName": "Fake Company",
            "industry": "Semiconductor",
            "sector": "Technology",
            "currentPrice": 600,
            "trailingPE": 20,
            "priceToBook": 4,
        }
        columns = pd.to_datetime(["2025-12-31", "2024-12-31"])
        self.financials = pd.DataFrame(
            {
                columns[0]: {
                    "Net Income": 120,
                    "Total Revenue": 500,
                    "Gross Profit": 250,
                    "Operating Income": 180,
                },
                columns[1]: {
                    "Net Income": 100,
                    "Total Revenue": 450,
                    "Gross Profit": 200,
                    "Operating Income": 160,
                },
            }
        )
        self.balance_sheet = pd.DataFrame(
            {
                columns[0]: {
                    "Total Assets": 1000,
                    "Stockholders Equity": 700,
                    "Total Debt": 100,
                    "Long Term Debt": 80,
                    "Current Assets": 400,
                    "Current Liabilities": 200,
                    "Ordinary Shares Number": 10,
                },
                columns[1]: {
                    "Total Assets": 900,
                    "Stockholders Equity": 650,
                    "Total Debt": 120,
                    "Long Term Debt": 100,
                    "Current Assets": 360,
                    "Current Liabilities": 220,
                    "Ordinary Shares Number": 10,
                },
            }
        )
        self.cashflow = pd.DataFrame(
            {
                columns[0]: {
                    "Operating Cash Flow": 150,
                    "Free Cash Flow": 80,
                },
                columns[1]: {
                    "Operating Cash Flow": 130,
                    "Free Cash Flow": 70,
                },
            }
        )

    def history(self, **kwargs):
        return pd.DataFrame(
            {"Close": [100, 105]},
            index=pd.to_datetime(["2025-01-01", "2025-01-02"]),
        )


if __name__ == "__main__":
    unittest.main()
