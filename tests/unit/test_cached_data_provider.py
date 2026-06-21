from datetime import datetime, timedelta, timezone
import unittest

from data_provider.cache import CacheKey, MemoryCache
from data_provider.cached_provider import CachedDataProvider
from models.financial_data import FinancialData, FinancialPeriod


class CachedDataProviderTests(unittest.TestCase):
    def test_first_call_uses_provider_second_call_uses_cache_hit(self):
        provider = CountingProvider()
        cached_provider = CachedDataProvider(provider=provider, cache=MemoryCache())

        first = cached_provider.get_financial_data("2330")
        second = cached_provider.get_financial_data("2330")

        self.assertEqual(provider.financial_calls, 1)
        self.assertIs(first, second)
        messages = diagnostic_messages(cached_provider)
        self.assertTrue(any("cache_miss" in message for message in messages))
        self.assertTrue(any("provider_called" in message for message in messages))
        self.assertTrue(any("cache_hit" in message for message in messages))

    def test_invalidate_forces_provider_to_be_called_again(self):
        provider = CountingProvider()
        cache = MemoryCache()
        cached_provider = CachedDataProvider(provider=provider, cache=cache)

        first = cached_provider.get_financial_data("2330")
        cache.invalidate(financial_key())
        second = cached_provider.get_financial_data("2330")

        self.assertEqual(provider.financial_calls, 2)
        self.assertNotEqual(first.company_name, second.company_name)

    def test_expired_ttl_forces_provider_to_be_called_again(self):
        clock = ManualClock(datetime(2026, 1, 1, tzinfo=timezone.utc))
        provider = CountingProvider()
        cache = MemoryCache(clock=clock.now)
        cached_provider = CachedDataProvider(
            provider=provider,
            cache=cache,
            ttl_seconds_by_data_type={"financials": 10},
        )

        first = cached_provider.get_financial_data("2330")
        clock.advance(seconds=11)
        second = cached_provider.get_financial_data("2330")

        self.assertEqual(provider.financial_calls, 2)
        self.assertNotEqual(first.company_name, second.company_name)
        messages = diagnostic_messages(cached_provider)
        self.assertTrue(any("cache_expired" in message for message in messages))
        self.assertEqual(
            [message for message in messages if "provider_called" in message],
            [
                "provider_called: fake:2330.TW:financials:annual::",
                "provider_called: fake:2330.TW:financials:annual::",
            ],
        )


class CountingProvider:
    name = "fake"

    def __init__(self):
        self.financial_calls = 0

    def get_financial_data(self, symbol, as_of=None):
        self.financial_calls += 1
        return FinancialData(
            symbol="2330.TW",
            company_name=f"Fake Company {self.financial_calls}",
            current=FinancialPeriod(period="2025-12-31", net_income=100),
        )

    def get_price_history(self, symbol, start, end):
        raise NotImplementedError

    def get_universe(self, universe_id):
        raise NotImplementedError

    def diagnostics(self):
        return []


class ManualClock:
    def __init__(self, current):
        self.current = current

    def now(self):
        return self.current

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)


def financial_key():
    return CacheKey(
        provider="fake",
        symbol="2330.TW",
        data_type="financials",
        period="annual",
    )


def diagnostic_messages(provider):
    return [diagnostic.message for diagnostic in provider.diagnostics()]


if __name__ == "__main__":
    unittest.main()
