from datetime import datetime, timedelta, timezone
import unittest

from data_provider.cache import CacheKey, MemoryCache


class MemoryCacheTests(unittest.TestCase):
    def test_cache_hit_returns_stored_value(self):
        cache = MemoryCache()
        key = make_key()
        value = {"company_name": "TSMC"}

        cache.set(key, value, ttl_seconds=60)

        self.assertTrue(cache.exists(key))
        self.assertEqual(cache.get(key), value)

    def test_cache_miss_returns_none(self):
        cache = MemoryCache()

        self.assertFalse(cache.exists(make_key()))
        self.assertIsNone(cache.get(make_key()))

    def test_expired_entry_is_not_returned(self):
        clock = ManualClock(datetime(2026, 1, 1, tzinfo=timezone.utc))
        cache = MemoryCache(clock=clock.now)
        key = make_key()
        cache.set(key, "old", ttl_seconds=10)

        clock.advance(seconds=11)

        self.assertFalse(cache.exists(key))
        self.assertIsNone(cache.get(key))
        self.assertIsNone(cache.entry(key))

    def test_invalidate_removes_single_entry(self):
        cache = MemoryCache()
        key = make_key()
        other_key = make_key(symbol="2454.TW")
        cache.set(key, "value")
        cache.set(other_key, "other")

        cache.invalidate(key)

        self.assertFalse(cache.exists(key))
        self.assertIsNone(cache.get(key))
        self.assertTrue(cache.exists(other_key))
        self.assertEqual(cache.get(other_key), "other")

    def test_clear_removes_all_entries(self):
        cache = MemoryCache()
        first_key = make_key(symbol="2330.TW")
        second_key = make_key(symbol="2454.TW")
        cache.set(first_key, "first")
        cache.set(second_key, "second")

        cache.clear()

        self.assertFalse(cache.exists(first_key))
        self.assertFalse(cache.exists(second_key))
        self.assertIsNone(cache.get(first_key))
        self.assertIsNone(cache.get(second_key))

    def test_cache_key_uses_canonical_string(self):
        key = CacheKey(
            provider=" Yahoo ",
            symbol="2330.tw",
            data_type=" Price_History ",
            period=" Daily ",
            start_date="2025-01-01",
            end_date="2025-12-31",
        )

        self.assertEqual(
            key.to_string(),
            "yahoo:2330.TW:price_history:daily:2025-01-01:2025-12-31",
        )


class ManualClock:
    def __init__(self, current):
        self.current = current

    def now(self):
        return self.current

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)


def make_key(symbol="2330.TW"):
    return CacheKey(
        provider="yahoo",
        symbol=symbol,
        data_type="info",
        period="none",
    )


if __name__ == "__main__":
    unittest.main()
