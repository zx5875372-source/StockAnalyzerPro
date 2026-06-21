from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from data_provider.cache.deserializer import deserialize_payload
from data_provider.cache.interfaces import CacheEntry, CacheKey, ICache
from data_provider.cache.serializer import serialize_payload


class SQLiteCache(ICache):
    def __init__(self, db_path: str | Path = "cache.db", clock: Callable[[], datetime] | None = None):
        self.db_path = Path(db_path)
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_schema()

    def get(self, key: CacheKey):
        row = self._fetch_row(key)
        if row is None:
            return None
        if self._is_row_expired(row):
            return None
        try:
            return self._deserialize_row(row)
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            return None

    def set(self, key: CacheKey, value, ttl_seconds: int | None = None) -> None:
        fetched_at = self._now()
        expires_at = None
        if ttl_seconds is not None:
            expires_at = fetched_at + timedelta(seconds=ttl_seconds)

        payload_json = self._payload_json(value)
        payload_hash = self._payload_hash(payload_json)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO cache_entries (
                    cache_key,
                    provider,
                    symbol,
                    data_type,
                    period,
                    start_date,
                    end_date,
                    fetched_at,
                    expires_at,
                    payload_json,
                    payload_hash,
                    schema_version
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    key.to_string(),
                    key.provider,
                    key.symbol,
                    key.data_type,
                    key.period,
                    key.start_date,
                    key.end_date,
                    self._datetime_to_text(fetched_at),
                    self._datetime_to_text(expires_at),
                    payload_json,
                    payload_hash,
                ),
            )

    def exists(self, key: CacheKey) -> bool:
        row = self._fetch_row(key)
        if row is None:
            return False
        if self._is_row_expired(row):
            return False
        try:
            self._validate_hash(row)
        except ValueError:
            return False
        return True

    def invalidate(self, key: CacheKey) -> None:
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM cache_entries WHERE cache_key = ?",
                (key.to_string(),),
            )

    def clear(self) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM cache_entries")

    def is_expired(self, key: CacheKey) -> bool:
        row = self._fetch_row(key)
        return row is not None and self._is_row_expired(row)

    def entry(self, key: CacheKey) -> CacheEntry | None:
        row = self._fetch_row(key)
        if row is None or self._is_row_expired(row):
            return None
        try:
            value = self._deserialize_row(row)
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            return None
        return CacheEntry(
            key=key,
            value=value,
            fetched_at=self._text_to_datetime(row["fetched_at"]),
            expires_at=self._text_to_datetime(row["expires_at"]),
        )

    def _initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cache_entries (
                    cache_key TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    symbol TEXT,
                    data_type TEXT NOT NULL,
                    period TEXT NOT NULL DEFAULT 'none',
                    start_date TEXT,
                    end_date TEXT,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT,
                    payload_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    schema_version INTEGER NOT NULL DEFAULT 1
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_cache_entries_lookup
                ON cache_entries (
                    provider,
                    symbol,
                    data_type,
                    period,
                    start_date,
                    end_date
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_cache_entries_expires_at
                ON cache_entries (expires_at)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_cache_entries_data_type
                ON cache_entries (data_type)
                """
            )

    def _fetch_row(self, key: CacheKey):
        with self._connect() as connection:
            return connection.execute(
                "SELECT * FROM cache_entries WHERE cache_key = ?",
                (key.to_string(),),
            ).fetchone()

    def _deserialize_row(self, row):
        self._validate_hash(row)
        envelope = json.loads(row["payload_json"])
        return deserialize_payload(envelope)

    def _validate_hash(self, row) -> None:
        payload_json = row["payload_json"]
        if self._payload_hash(payload_json) != row["payload_hash"]:
            raise ValueError("Cache payload hash mismatch")

    def _is_row_expired(self, row) -> bool:
        expires_at = self._text_to_datetime(row["expires_at"])
        return expires_at is not None and self._now() >= expires_at

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _payload_json(self, value) -> str:
        envelope = serialize_payload(value)
        return json.dumps(envelope, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _payload_hash(payload_json: str) -> str:
        return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()

    @staticmethod
    def _datetime_to_text(value: datetime | None) -> str | None:
        if value is None:
            return None
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def _text_to_datetime(value: str | None) -> datetime | None:
        if value is None:
            return None
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
