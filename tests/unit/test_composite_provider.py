import json
import unittest

import pandas as pd

from data_provider import CachedDataProvider, ProviderError, create_provider
from data_provider.interfaces import PriceHistory
from data_provider.providers.composite_provider import CompositeProvider
from models.financial_data import FinancialData, FinancialPeriod


class CompositeProviderTests(unittest.TestCase):
    def test_taiwan_stock_uses_finmind_primary_when_successful(self):
        finmind_data = financial_data("2330.TW", "finmind")
        yahoo_data = financial_data("2330.TW", "yahoo")
        finmind = FakeProvider("finmind", financial_data=finmind_data)
        yahoo = FakeProvider("yahoo", financial_data=yahoo_data)
        provider = CompositeProvider(primary_provider=finmind, fallback_provider=yahoo)

        result = provider.get_financial_data("2330")

        self.assertIs(result, finmind_data)
        self.assertEqual(finmind.financial_calls, [("2330.TW", None)])
        self.assertEqual(yahoo.financial_calls, [("2330.TW", None)])
        route = provider.routing_diagnostics()[0]
        self.assertEqual(route["primary_provider"], "finmind")
        self.assertEqual(route["fallback_provider"], "yahoo")
        self.assertEqual(route["selected_provider"], "finmind")
        self.assertFalse(route["fallback_used"])
        self.assertIsNone(route["fallback_reason"])
        self.assertEqual(route["symbol_type"], "taiwan_stock")
        self.assertEqual(route["source_chain"], ["finmind"])

    def test_taiwan_stock_falls_back_to_yahoo_when_finmind_fails(self):
        yahoo_data = financial_data("2330.TW", "yahoo")
        finmind = FakeProvider("finmind", failure=ProviderError("FinMind missing financial rows"))
        yahoo = FakeProvider("yahoo", financial_data=yahoo_data)
        provider = CompositeProvider(primary_provider=finmind, fallback_provider=yahoo)

        result = provider.get_financial_data("2330")

        self.assertIs(result, yahoo_data)
        self.assertEqual(finmind.financial_calls, [("2330.TW", None)])
        self.assertEqual(yahoo.financial_calls, [("2330.TW", None)])
        route = provider.routing_diagnostics()[0]
        self.assertEqual(route["selected_provider"], "yahoo")
        self.assertTrue(route["fallback_used"])
        self.assertEqual(route["fallback_reason"], "FinMind missing financial rows")
        self.assertEqual(route["source_chain"], ["finmind", "yahoo"])
        provider_diagnostic = provider.diagnostics()[0]
        self.assertEqual(provider_diagnostic.severity, "warning")
        self.assertEqual(json.loads(provider_diagnostic.message)["fallback_reason"], "FinMind missing financial rows")

    def test_non_taiwan_stock_goes_directly_to_yahoo(self):
        yahoo_data = financial_data("AAPL", "yahoo")
        finmind = FakeProvider("finmind", financial_data=financial_data("AAPL", "finmind"))
        yahoo = FakeProvider("yahoo", financial_data=yahoo_data)
        provider = CompositeProvider(primary_provider=finmind, fallback_provider=yahoo)

        result = provider.get_financial_data("AAPL")

        self.assertIs(result, yahoo_data)
        self.assertEqual(finmind.financial_calls, [])
        self.assertEqual(yahoo.financial_calls, [("AAPL", None)])
        route = provider.routing_diagnostics()[0]
        self.assertEqual(route["selected_provider"], "yahoo")
        self.assertFalse(route["fallback_used"])
        self.assertEqual(route["symbol_type"], "non_taiwan")
        self.assertEqual(route["source_chain"], ["yahoo"])

    def test_price_history_always_uses_yahoo(self):
        frame = pd.DataFrame({"Close": [100, 101]})
        price_history = PriceHistory(symbol="2330.TW", data=frame, start="2024-01-01", end="2024-01-31")
        finmind = FakeProvider("finmind", financial_data=financial_data("2330.TW", "finmind"))
        yahoo = FakeProvider("yahoo", price_history=price_history)
        provider = CompositeProvider(primary_provider=finmind, fallback_provider=yahoo)

        result = provider.get_price_history("2330", "2024-01-01", "2024-01-31")

        self.assertIs(result, price_history)
        self.assertEqual(finmind.price_calls, [])
        self.assertEqual(yahoo.price_calls, [("2330.TW", "2024-01-01", "2024-01-31")])
        route = provider.routing_diagnostics()[0]
        self.assertEqual(route["selected_provider"], "yahoo")
        self.assertFalse(route["fallback_used"])
        self.assertEqual(route["source_chain"], ["yahoo"])

    def test_factory_creates_composite_provider(self):
        provider = create_provider("composite")

        self.assertIsInstance(provider, CompositeProvider)

    def test_yahoo_enrichment_fills_current_price_and_metadata(self):
        finmind_data = FinancialData(
            symbol="2330.TW",
            company_name=None,
            current=FinancialPeriod(period="2024-12-31", eps=10, book_value_per_share=50),
        )
        yahoo_data = FinancialData(
            symbol="2330.TW",
            company_name="Taiwan Semiconductor Manufacturing Company Limited",
            industry="Semiconductors",
            sector="Technology",
            price=100,
            current=FinancialPeriod(period="2024-12-31"),
        )
        provider = CompositeProvider(
            primary_provider=FakeProvider("finmind", financial_data=finmind_data),
            fallback_provider=FakeProvider("yahoo", financial_data=yahoo_data),
        )

        result = provider.get_financial_data("2330")

        self.assertEqual(result.company_name, "台積電")
        self.assertEqual(result.industry, "Semiconductors")
        self.assertEqual(result.sector, "Technology")
        self.assertEqual(result.price, 100)
        self.assertIn("yahoo_enriched_fields:", "\n".join(result.diagnostics))

    def test_pe_and_pb_are_derived_from_yahoo_price_and_finmind_eps_bvps(self):
        finmind_data = FinancialData(
            symbol="2330.TW",
            current=FinancialPeriod(period="2024-12-31", eps=10, book_value_per_share=50),
        )
        yahoo_data = FinancialData(
            symbol="2330.TW",
            price=100,
            current=FinancialPeriod(period="2024-12-31"),
        )
        provider = CompositeProvider(
            primary_provider=FakeProvider("finmind", financial_data=finmind_data),
            fallback_provider=FakeProvider("yahoo", financial_data=yahoo_data),
        )

        result = provider.get_financial_data("2330")

        self.assertEqual(result.price, 100)
        self.assertEqual(result.pe, 10)
        self.assertEqual(result.pb, 2)
        diagnostics_text = "\n".join(result.diagnostics)
        self.assertIn("derived_fields: pb, pe", diagnostics_text)

    def test_taiwan_name_fallback_handles_6285(self):
        finmind_data = FinancialData(
            symbol="6285.TW",
            company_name=None,
            current=FinancialPeriod(period="2024-12-31"),
        )
        yahoo_data = FinancialData(
            symbol="6285.TW",
            company_name=None,
            current=FinancialPeriod(period="2024-12-31"),
        )
        provider = CompositeProvider(
            primary_provider=FakeProvider("finmind", financial_data=finmind_data),
            fallback_provider=FakeProvider("yahoo", financial_data=yahoo_data),
        )

        result = provider.get_financial_data("6285")

        self.assertEqual(result.company_name, "啟碁")
        self.assertIn("company_name_fallback: 啟碁", result.diagnostics)

    def test_cached_yahoo_default_provider_is_unchanged(self):
        provider = create_provider("cached_yahoo")

        self.assertIsInstance(provider, CachedDataProvider)


class FakeProvider:
    def __init__(
        self,
        name,
        financial_data=None,
        price_history=None,
        failure=None,
    ):
        self.name = name
        self.financial_data = financial_data
        self.price_history = price_history
        self.failure = failure
        self.financial_calls = []
        self.price_calls = []

    def get_financial_data(self, symbol: str, as_of: str | None = None):
        self.financial_calls.append((symbol, as_of))
        if self.failure:
            raise self.failure
        return self.financial_data

    def get_price_history(self, symbol: str, start: str, end: str):
        self.price_calls.append((symbol, start, end))
        if self.failure:
            raise self.failure
        return self.price_history

    def get_universe(self, universe_id: str):
        raise ProviderError("not implemented")

    def diagnostics(self):
        return []


def financial_data(symbol: str, company_name: str):
    return FinancialData(
        symbol=symbol,
        company_name=company_name,
        current=FinancialPeriod(period="2024-12-31", net_income=100),
    )


if __name__ == "__main__":
    unittest.main()
