from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class CacheKey:
    provider: str
    symbol: str
    data_type: str
    period: str = "none"
    start_date: str | None = None
    end_date: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "provider", self.provider.strip().lower())
        object.__setattr__(self, "symbol", self.symbol.strip().upper())
        object.__setattr__(self, "data_type", self.data_type.strip().lower())
        object.__setattr__(self, "period", (self.period or "none").strip().lower())
        object.__setattr__(self, "start_date", self.start_date or "")
        object.__setattr__(self, "end_date", self.end_date or "")

    def to_string(self) -> str:
        return ":".join(
            [
                self.provider,
                self.symbol,
                self.data_type,
                self.period,
                self.start_date,
                self.end_date,
            ]
        )


@dataclass(frozen=True)
class CacheEntry:
    key: CacheKey
    value: Any
    fetched_at: datetime
    expires_at: datetime | None = None

    def is_expired(self, now: datetime) -> bool:
        return self.expires_at is not None and now >= self.expires_at


class ICache(ABC):
    @abstractmethod
    def get(self, key: CacheKey):
        raise NotImplementedError

    @abstractmethod
    def set(self, key: CacheKey, value, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def exists(self, key: CacheKey) -> bool:
        raise NotImplementedError

    @abstractmethod
    def invalidate(self, key: CacheKey) -> None:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError
