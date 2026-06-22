from __future__ import annotations

from dataclasses import dataclass


DEFAULT_FINMIND_BASE_URL = "https://api.finmindtrade.com/api/v4/data"


@dataclass
class FinMindConfig:
    base_url: str = DEFAULT_FINMIND_BASE_URL
    token: str | None = None
    timeout: int = 30
    max_retry: int = 3
