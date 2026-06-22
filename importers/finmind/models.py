from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FinMindResponse:
    status: int
    message: str
    data: list[dict] = field(default_factory=list)
