import unittest

from importers.finmind import (
    DEFAULT_FINMIND_BASE_URL,
    FinMindAPIError,
    FinMindAuthenticationError,
    FinMindClient,
    FinMindConfig,
    FinMindError,
    FinMindRateLimitError,
    FinMindResponse,
    FinMindSession,
)
from importers import FinMindImporter


class MockResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload


class MockSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append({"url": url, "params": dict(params), "timeout": timeout})
        if not self.responses:
            raise AssertionError("No mock response available")
        return self.responses.pop(0)


class FinMindClientTests(unittest.TestCase):
    def test_config_defaults(self):
        config = FinMindConfig()

        self.assertEqual(config.base_url, DEFAULT_FINMIND_BASE_URL)
        self.assertIsNone(config.token)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retry, 3)

    def test_client_initialization_uses_config(self):
        config = FinMindConfig(
            base_url="https://example.test/api",
            token="test-token",
            timeout=10,
            max_retry=5,
        )

        client = FinMindClient(config=config)

        self.assertEqual(client.config, config)
        self.assertEqual(client.base_url, "https://example.test/api")
        self.assertEqual(client.token, "test-token")
        self.assertEqual(client.timeout, 10)
        self.assertEqual(client.max_retry, 5)
        self.assertIsInstance(client.session, FinMindSession)
        self.assertEqual(client.session.headers["Authorization"], "Bearer test-token")

    def test_client_accepts_custom_session(self):
        session = FinMindSession(headers={"X-Test": "yes"})

        client = FinMindClient(session=session)

        self.assertIs(client.session, session)
        self.assertEqual(client.session.headers["X-Test"], "yes")

    def test_success_response(self):
        session = MockSession(
            [
                MockResponse(
                    200,
                    {
                        "status": 200,
                        "msg": "success",
                        "data": [{"stock_id": "2330", "date": "2025-12-31"}],
                    },
                )
            ]
        )
        client = FinMindClient(
            config=FinMindConfig(token="token-1", timeout=12, max_retry=0),
            session=session,
        )

        response = client.get_financial_statement("2330", start_date="2025-01-01", end_date="2025-12-31")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.message, "success")
        self.assertEqual(response.data[0]["stock_id"], "2330")
        self.assertEqual(session.calls[0]["url"], DEFAULT_FINMIND_BASE_URL)
        self.assertEqual(session.calls[0]["timeout"], 12)
        self.assertEqual(
            session.calls[0]["params"],
            {
                "dataset": "TaiwanStockFinancialStatements",
                "data_id": "2330",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "token": "token-1",
            },
        )

    def test_balance_sheet_and_cash_flow_methods_use_expected_datasets(self):
        session = MockSession(
            [
                MockResponse(200, {"status": 200, "msg": "success", "data": []}),
                MockResponse(200, {"status": 200, "msg": "success", "data": []}),
            ]
        )
        client = FinMindClient(config=FinMindConfig(max_retry=0), session=session)

        client.get_balance_sheet("2330")
        client.get_cash_flow("2330")

        self.assertEqual(session.calls[0]["params"]["dataset"], "TaiwanStockBalanceSheet")
        self.assertEqual(session.calls[1]["params"]["dataset"], "TaiwanStockCashFlowsStatement")

    def test_http_error_raises_api_error(self):
        session = MockSession([MockResponse(500, {"status": 500, "msg": "server error", "data": []})])
        client = FinMindClient(config=FinMindConfig(max_retry=0), session=session)

        with self.assertRaisesRegex(FinMindAPIError, "server error"):
            client.get_financial_statement("2330")

    def test_rate_limit_error_retries_then_raises(self):
        session = MockSession(
            [
                MockResponse(429, {"status": 429, "msg": "rate limited", "data": []}),
                MockResponse(429, {"status": 429, "msg": "rate limited", "data": []}),
            ]
        )
        client = FinMindClient(config=FinMindConfig(max_retry=1), session=session)

        with self.assertRaises(FinMindRateLimitError):
            client.get_financial_statement("2330")

        self.assertEqual(len(session.calls), 2)

    def test_auth_error_does_not_retry(self):
        session = MockSession([MockResponse(401, {"status": 401, "msg": "bad token", "data": []})])
        client = FinMindClient(config=FinMindConfig(max_retry=3), session=session)

        with self.assertRaises(FinMindAuthenticationError):
            client.get_financial_statement("2330")

        self.assertEqual(len(session.calls), 1)

    def test_retry_success_after_transient_error(self):
        session = MockSession(
            [
                MockResponse(500, {"status": 500, "msg": "server error", "data": []}),
                MockResponse(200, {"status": 200, "msg": "success", "data": [{"stock_id": "2330"}]}),
            ]
        )
        client = FinMindClient(config=FinMindConfig(max_retry=1), session=session)

        response = client.get_financial_statement("2330")

        self.assertEqual(response.status, 200)
        self.assertEqual(response.data, [{"stock_id": "2330"}])
        self.assertEqual(len(session.calls), 2)

    def test_request_requires_stock_id(self):
        client = FinMindClient(config=FinMindConfig(max_retry=0), session=MockSession([]))

        with self.assertRaisesRegex(FinMindAPIError, "requires stock_id"):
            client.request("TaiwanStockFinancialStatements")

    def test_exception_hierarchy(self):
        self.assertTrue(issubclass(FinMindAPIError, FinMindError))
        self.assertTrue(issubclass(FinMindRateLimitError, FinMindAPIError))
        self.assertTrue(issubclass(FinMindAuthenticationError, FinMindAPIError))

    def test_response_model(self):
        response = FinMindResponse(
            status=200,
            message="success",
            data=[{"stock_id": "2330", "date": "2025-12-31"}],
        )

        self.assertEqual(response.status, 200)
        self.assertEqual(response.message, "success")
        self.assertEqual(response.data[0]["stock_id"], "2330")

    def test_finmind_importer_uses_client(self):
        client = FinMindClient()

        importer = FinMindImporter(client=client)

        self.assertIs(importer.client, client)


if __name__ == "__main__":
    unittest.main()
