from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from data_provider.cache.interfaces import CacheEntry, CacheKey, ICache


class MemoryCache(ICache):
    def __init__(self, clock: Callable[[], datetime] | None = None):
        self._entries: dict[CacheKey, CacheEntry] = {}
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def get(self, key: CacheKey):
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.is_expired(self._now()):
            self.invalidate(key)
            return None
        return entry.value

    def set(self, key: CacheKey, value, ttl_seconds: int | None = None) -> None:
        fetched_at = self._now()
        expires_at = None
        if ttl_seconds is not None:
            expires_at = fetched_at + timedelta(seconds=ttl_seconds)

        self._entries[key] = CacheEntry(
            key=key,
            value=value,
            fetched_at=fetched_at,
            expires_at=expires_at,
        )

    def exists(self, key: CacheKey) -> bool:
        entry = self._entries.get(key)
        if entry is None:
            return False
        if entry.is_expired(self._now()):
            self.invalidate(key)
            return False
        return True

    def invalidate(self, key: CacheKey) -> None:
        self._entries.pop(key, None)

    def clear(self) -> None:
        self._entries.clear()

    def is_expired(self, key: CacheKey) -> bool:
        entry = self._entries.get(key)
        return entry is not None and entry.is_expired(self._now())

    def entry(self, key: CacheKey) -> CacheEntry | None:
        entry = self._entries.get(key)
        if entry is None or entry.is_expired(self._now()):
            return None
        return entry

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
