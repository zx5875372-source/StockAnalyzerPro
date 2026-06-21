from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from importers.import_result import ImportResult


class ImporterError(ValueError):
    pass


class BaseImporter(ABC):
    name: str = "base"
    version: str = "v0"

    @abstractmethod
    def supports(self, snapshot_type: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def import_snapshot(
        self,
        source: str | Path,
        snapshot_type: str | None = None,
    ) -> ImportResult:
        raise NotImplementedError

    @abstractmethod
    def import_financial_statements(self, source: str | Path) -> ImportResult:
        raise NotImplementedError
