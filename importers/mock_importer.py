from __future__ import annotations

from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from importers.base_importer import BaseImporter
from importers.import_result import ImportResult


class MockImporter(BaseImporter):
    name = "mock"
    version = "v0"

    def __init__(
        self,
        financial_statement_snapshots: list[FinancialStatementSnapshot] | None = None,
        sap_score_snapshots: list[SAPScoreSnapshot] | None = None,
    ):
        self._financial_statement_snapshots = financial_statement_snapshots or []
        self._sap_score_snapshots = sap_score_snapshots or []

    def supports(self, snapshot_type: str) -> bool:
        return _normalize_snapshot_type(snapshot_type) in {"financial_statement", "sap_score"}

    def import_snapshot(
        self,
        source: str | Path = "mock",
        snapshot_type: str | None = None,
    ) -> ImportResult:
        resolved_type = _normalize_snapshot_type(snapshot_type) if snapshot_type else None
        financial_snapshots = []
        sap_snapshots = []

        if resolved_type in {None, "financial_statement"}:
            financial_snapshots = list(self._financial_statement_snapshots)
        if resolved_type in {None, "sap_score"}:
            sap_snapshots = list(self._sap_score_snapshots)

        return ImportResult(
            importer=self.name,
            importer_version=self.version,
            source=str(source),
            imported_count=len(financial_snapshots) + len(sap_snapshots),
            financial_statement_snapshots=financial_snapshots,
            sap_score_snapshots=sap_snapshots,
        )

    def import_financial_statements(self, source: str | Path = "mock") -> ImportResult:
        return self.import_snapshot(source=source, snapshot_type="financial_statement")


def _normalize_snapshot_type(snapshot_type: str) -> str:
    return snapshot_type.strip().lower().replace("-", "_")
