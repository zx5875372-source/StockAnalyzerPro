from __future__ import annotations

from pathlib import Path

from importers.base_importer import BaseImporter
from importers.finmind import FinMindClient
from importers.import_result import ImportResult


class FinMindImporter(BaseImporter):
    name = "finmind"
    version = "v0-architecture"

    def __init__(self, client: FinMindClient | None = None):
        self.client = client or FinMindClient()

    def supports(self, snapshot_type: str) -> bool:
        normalized = snapshot_type.strip().lower().replace("-", "_")
        return normalized in {
            "financial",
            "financial_statement",
            "financial_statements",
            "financial_statement_snapshot",
            "sap",
            "sap_score",
            "sap_score_snapshot",
        }

    def import_snapshot(
        self,
        source: str | Path,
        snapshot_type: str | None = None,
    ) -> ImportResult:
        raise NotImplementedError("FinMindImporter is architecture-only and does not call the FinMind API yet")

    def import_financial_statements(self, source: str | Path) -> ImportResult:
        raise NotImplementedError("FinMindImporter is architecture-only and does not call the FinMind API yet")
