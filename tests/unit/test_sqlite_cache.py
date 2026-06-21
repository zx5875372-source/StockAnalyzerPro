from datetime import datetime, timedelta, timezone
from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from data_provider.cache import CacheKey, SQLiteCache
from data_provider.cache.serializer import CacheSerializationError
from data_provider.interfaces import PriceHistory
from models.financial_data import FinancialData, FinancialPeriod


class SQLiteCacheTests(unittest.TestCase):
    def test_set_get_dict_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SQLiteCache(Path(temp_dir) / "cache.db")
            key = make_key(data_type="info")
            payload = {"company_name": "TSMC", "price": 600}

            cache.set(key, payload, ttl_seconds=60)

            self.assertTrue(cache.exists(key))
            self.assertEqual(cache.get(key), payload)

    def test_cache_persists_across_instances(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "cache.db"
            key = make_key(data_type="info")
            SQLiteCache(db_path).set(key, {"value": 1}, ttl_seconds=60)

            reloaded_cache = SQLiteCache(db_path)

            self.assertEqual(reloaded_cache.get(key), {"value": 1})

    def test_set_get_financial_data_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SQLiteCache(Path(temp_dir) / "cache.db")
            key = make_key(data_type="financials")
            payload = FinancialData(
                symbol="2330.TW",
                company_name="TSMC",
                industry="Semiconductor",
                sector="Technology",
                price=600,
                pe=20,
                pb=4,
                current=FinancialPeriod(period="2025-12-31", net_income=100, total_assets=1000),
                previous=FinancialPeriod(period="2024-12-31", net_income=90, total_assets=900),
                missing_fields=["current.free_cashflow"],
                diagnostics=["sample diagnostic"],
            )

            cache.set(key, payload, ttl_seconds=60)
            result = cache.get(key)

            self.assertIsInstance(result, FinancialData)
            self.assertEqual(result.symbol, "2330.TW")
            self.assertEqual(result.company_name, "TSMC")
            self.assertEqual(result.current.net_income, 100)
            self.assertEqual(result.previous.net_income, 90)
            self.assertEqual(result.missing_fields, ["current.free_cashflow"])
            self.assertEqual(result.diagnostics, ["sample diagnostic"])

    def test_set_get_price_history_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SQLiteCache(Path(temp_dir) / "cache.db")
            key = make_key(data_type="price_history", start_date="2025-01-01", end_date="2025-01-31")
            frame = pd.DataFrame(
                {"Close": [100.0, 105.0], "Volume": [1000, 1200]},
                index=pd.to_datetime(["2025-01-02", "2025-01-03"]),
            )
            payload = PriceHistory(symbol="2330.TW", data=frame, start="2025-01-01", end="2025-01-31")

            cache.set(key, payload, ttl_seconds=60)
            result = cache.get(key)

            self.assertIsInstance(result, PriceHistory)
            self.assertEqual(result.symbol, "2330.TW")
            self.assertEqual(result.start, "2025-01-01")
            self.assertEqual(result.end, "2025-01-31")
            pd.testing.assert_frame_equal(result.data, frame)

    def test_invalidate_removes_entry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SQLiteCache(Path(temp_dir) / "cache.db")
            key = make_key()
            cache.set(key, {"value": 1})

            cache.invalidate(key)

            self.assertFalse(cache.exists(key))
            self.assertIsNone(cache.get(key))

    def test_clear_removes_all_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SQLiteCache(Path(temp_dir) / "cache.db")
            first_key = make_key(symbol="2330.TW")
            second_key = make_key(symbol="2454.TW")
            cache.set(first_key, {"value": 1})
            cache.set(second_key, {"value": 2})

            cache.clear()

            self.assertFalse(cache.exists(first_key))
            self.assertFalse(cache.exists(second_key))
            self.assertIsNone(cache.get(first_key))
            self.assertIsNone(cache.get(second_key))

    def test_expired_entry_is_not_returned(self):
        clock = ManualClock(datetime(2026, 1, 1, tzinfo=timezone.utc))
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SQLiteCache(Path(temp_dir) / "cache.db", clock=clock.now)
            key = make_key()
            cache.set(key, {"value": "old"}, ttl_seconds=10)

            clock.advance(seconds=11)

            self.assertTrue(cache.is_expired(key))
            self.assertFalse(cache.exists(key))
            self.assertIsNone(cache.get(key))

    def test_first_use_creates_cache_db_and_table(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "cache.db"

            SQLiteCache(db_path)

            self.assertTrue(db_path.exists())
            with closing(sqlite3.connect(db_path)) as connection:
                table_count = connection.execute(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = 'cache_entries'"
                ).fetchone()[0]
            self.assertEqual(table_count, 1)

    def test_hash_mismatch_returns_cache_miss(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "cache.db"
            cache = SQLiteCache(db_path)
            key = make_key()
            cache.set(key, {"value": 1})

            with closing(sqlite3.connect(db_path)) as connection:
                connection.execute(
                    "UPDATE cache_entries SET payload_json = ? WHERE cache_key = ?",
                    ('{"type":"JSON","schema_version":1,"payload":{"value":2}}', key.to_string()),
                )
                connection.commit()

            self.assertFalse(cache.exists(key))
            self.assertIsNone(cache.get(key))

    def test_dataframe_payload_is_not_supported_directly(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = SQLiteCache(Path(temp_dir) / "cache.db")

            with self.assertRaises(CacheSerializationError):
                cache.set(make_key(), pd.DataFrame({"Close": [100]}))


class ManualClock:
    def __init__(self, current):
        self.current = current

    def now(self):
        return self.current

    def advance(self, seconds):
        self.current += timedelta(seconds=seconds)


def make_key(
    symbol="2330.TW",
    data_type="info",
    start_date=None,
    end_date=None,
):
    return CacheKey(
        provider="yahoo",
        symbol=symbol,
        data_type=data_type,
        period="daily" if data_type == "price_history" else "none",
        start_date=start_date,
        end_date=end_date,
    )


if __name__ == "__main__":
    unittest.main()
