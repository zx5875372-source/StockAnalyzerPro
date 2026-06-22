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

    def test_request_methods_are_not_implemented_yet(self):
        client = FinMindClient()

        with self.assertRaisesRegex(NotImplementedError, "not implemented"):
            client.request("TaiwanStockFinancialStatements")

        with self.assertRaisesRegex(NotImplementedError, "not implemented"):
            client.get_financial_statements("2330", "2025-01-01", "2025-12-31")

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
