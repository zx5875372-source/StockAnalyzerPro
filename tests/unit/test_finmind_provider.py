import unittest

from data_provider import CachedDataProvider, ProviderError, create_provider
from data_provider.providers.finmind_provider import FinMindProvider
from importers.finmind import FinMindResponse


class FinMindProviderTests(unittest.TestCase):
    def test_factory_creates_finmind_provider(self):
        provider = create_provider("finmind")

        self.assertIsInstance(provider, FinMindProvider)

    def test_metadata_and_initial_diagnostics(self):
        provider = FinMindProvider(client=FakeFinMindClient())

        self.assertEqual(provider.name, "finmind")
        self.assertEqual(provider.version, "financial-mapping-v1")
        self.assertEqual(provider.diagnostics(), [])
        self.assertEqual(provider.get_provider_diagnostics(), [])

    def test_mock_client_valid_response_builds_financial_data(self):
        client = FakeFinMindClient(
            financial_statement_rows=[
                wide_row("2024-12-31", revenue=3000, net_income=900, gross_profit=1500, eps=9),
                wide_row("2023-12-31", revenue=2500, net_income=700, gross_profit=1200, eps=7),
            ],
            balance_sheet_rows=[
                wide_row("2024-12-31", total_assets=10000, total_liabilities=3500, total_equity=6500, shares_outstanding=100),
                wide_row("2023-12-31", total_assets=9000, total_liabilities=3300, total_equity=5700, shares_outstanding=100),
            ],
            cash_flow_rows=[
                wide_row("2024-12-31", cash_from_operations=1200, capital_expenditure=300),
                wide_row("2023-12-31", cash_from_operations=1000, capital_expenditure=250),
            ],
        )
        provider = FinMindProvider(client=client)

        result = provider.get_financial_data("2330")

        self.assertEqual(result.symbol, "2330.TW")
        self.assertEqual(result.company_name, "台積電")
        self.assertEqual(result.current.period, "2024-12-31")
        self.assertEqual(result.previous.period, "2023-12-31")
        self.assertEqual(result.current.revenue, 3000)
        self.assertEqual(result.current.net_income, 900)
        self.assertEqual(result.current.total_assets, 10000)
        self.assertEqual(result.current.total_debt, 3500)
        self.assertEqual(result.current.total_equity, 6500)
        self.assertEqual(result.current.operating_cashflow, 1200)
        self.assertEqual(result.current.free_cashflow, 900)
        self.assertEqual(result.current.gross_profit, 1500)
        self.assertEqual(result.current.shares_outstanding, 100)
        self.assertEqual(result.current.eps, 9)
        self.assertEqual(result.current.book_value_per_share, 65)
        self.assertIn("FinMindProvider mapped 6 raw rows", result.diagnostics[0])
        self.assertEqual(client.requested_financial_statement_symbols, ["2330"])
        self.assertEqual(client.requested_balance_sheet_symbols, ["2330"])
        self.assertEqual(client.requested_cash_flow_symbols, ["2330"])

    def test_long_form_rows_and_roc_year_quarter_build_periods(self):
        client = FakeFinMindClient(
            financial_statement_rows=[
                long_row(113, "Q4", "營業收入", 3000),
                long_row(113, "Q4", "本期淨利", 900),
                long_row(113, "Q4", "營業毛利", 1500),
                long_row(112, "Q4", "營業收入", 2500),
                long_row(112, "Q4", "本期淨利", 700),
                long_row(112, "Q4", "營業毛利", 1200),
            ],
            balance_sheet_rows=[
                long_row(113, "Q4", "資產總額", 10000),
                long_row(113, "Q4", "負債總額", 3500),
                long_row(113, "Q4", "股本", 100),
                long_row(112, "Q4", "資產總額", 9000),
                long_row(112, "Q4", "負債總額", 3300),
                long_row(112, "Q4", "股本", 100),
            ],
            cash_flow_rows=[
                long_row(113, "Q4", "營業活動現金流量", 1200),
                long_row(113, "Q4", "資本支出", -300),
                long_row(112, "Q4", "營業活動現金流量", 1000),
                long_row(112, "Q4", "資本支出", -250),
            ],
        )
        provider = FinMindProvider(client=client)

        result = provider.get_financial_data("2330.TW")

        self.assertEqual(result.current.period, "2024-12-31")
        self.assertEqual(result.previous.period, "2023-12-31")
        self.assertEqual(result.current.total_equity, 6500)
        self.assertEqual(result.current.free_cashflow, 900)
        self.assertEqual(result.current.eps, 9)

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

    def test_empty_finmind_response_has_clear_diagnostic(self):
        provider = FinMindProvider(client=object())

        with self.assertRaisesRegex(ProviderError, "no FinMind financial rows returned"):
            provider.get_financial_data("2330")

        diagnostics = provider.get_provider_diagnostics()
        self.assertEqual(diagnostics[0].symbol, "2330.TW")
        self.assertIn("Yahoo fallback", diagnostics[0].message)

    def test_missing_fields_are_recorded_in_result_and_provider_diagnostics(self):
        provider = FinMindProvider(
            client=FakeFinMindClient(
                financial_statement_rows=[
                    wide_row("2024-12-31", revenue=3000, net_income=900),
                    wide_row("2023-12-31", revenue=2500, net_income=700),
                ]
            )
        )

        result = provider.get_financial_data("2330")

        self.assertIn("current.total_assets", result.missing_fields)
        self.assertIn("previous.total_assets", result.missing_fields)
        self.assertTrue(any("missing fields:" in item for item in result.diagnostics))
        provider_diagnostics = provider.get_provider_diagnostics()
        self.assertEqual(provider_diagnostics[0].severity, "warning")
        self.assertIn("current.total_assets", provider_diagnostics[0].message)

    def test_missing_date_range_uses_safe_defaults(self):
        client = FakeFinMindClient(
            financial_statement_rows=[
                wide_row("2024-12-31", revenue=3000, net_income=900),
            ],
        )
        provider = FinMindProvider(client=client)

        provider.get_financial_data("2330")

        stock_id, start_date, end_date = client.financial_statement_calls[0]
        self.assertEqual(stock_id, "2330")
        self.assertRegex(start_date, r"^\d{4}-\d{2}-\d{2}$")
        self.assertRegex(end_date, r"^\d{4}-\d{2}-\d{2}$")

    def test_explicit_date_range_is_forwarded_to_finmind_client(self):
        client = FakeFinMindClient(
            financial_statement_rows=[
                wide_row("2024-12-31", revenue=3000, net_income=900),
            ],
        )
        provider = FinMindProvider(client=client)

        provider.get_financial_data("2330", start_date="2022-01-01", end_date="2024-12-31")

        self.assertEqual(client.financial_statement_calls[0], ("2330", "2022-01-01", "2024-12-31"))

    def test_symbol_helpers(self):
        self.assertEqual(FinMindProvider.normalize_symbol("2330"), "2330.TW")
        self.assertTrue(FinMindProvider.is_taiwan_symbol("6290.TWO"))
        self.assertFalse(FinMindProvider.is_taiwan_symbol("AAPL"))
        self.assertEqual(FinMindProvider.finmind_stock_id("2330.TW"), "2330")

    def test_cached_yahoo_default_provider_is_unchanged(self):
        provider = create_provider("cached_yahoo")

        self.assertIsInstance(provider, CachedDataProvider)


class FakeFinMindClient:
    def __init__(
        self,
        financial_statement_rows=None,
        balance_sheet_rows=None,
        cash_flow_rows=None,
    ):
        self.financial_statement_rows = financial_statement_rows or []
        self.balance_sheet_rows = balance_sheet_rows or []
        self.cash_flow_rows = cash_flow_rows or []
        self.requested_financial_statement_symbols = []
        self.requested_balance_sheet_symbols = []
        self.requested_cash_flow_symbols = []
        self.financial_statement_calls = []

    def get_financial_statement(self, stock_id: str, start_date=None, end_date=None):
        self.requested_financial_statement_symbols.append(stock_id)
        self.financial_statement_calls.append((stock_id, start_date, end_date))
        return FinMindResponse(status=200, message="", data=self.financial_statement_rows)

    def get_balance_sheet(self, stock_id: str, start_date=None, end_date=None):
        self.requested_balance_sheet_symbols.append(stock_id)
        return FinMindResponse(status=200, message="", data=self.balance_sheet_rows)

    def get_cash_flow(self, stock_id: str, start_date=None, end_date=None):
        self.requested_cash_flow_symbols.append(stock_id)
        return FinMindResponse(status=200, message="", data=self.cash_flow_rows)

    def get_company_info(self, stock_id: str):
        return {"company_name": "台積電"} if stock_id == "2330" else {}


def wide_row(statement_date: str, **fields):
    row = {"date": statement_date}
    row.update(fields)
    return row


def long_row(fiscal_year, fiscal_quarter, name, value):
    return {
        "fiscal_year": fiscal_year,
        "fiscal_quarter": fiscal_quarter,
        "name": name,
        "value": value,
    }


if __name__ == "__main__":
    unittest.main()
