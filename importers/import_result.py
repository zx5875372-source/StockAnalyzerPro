from __future__ import annotations

from dataclasses import dataclass, field

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot


@dataclass
class ImportResult:
    importer: str
    importer_version: str
    source: str
    imported_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    financial_statement_snapshots: list[FinancialStatementSnapshot] = field(default_factory=list)
    sap_score_snapshots: list[SAPScoreSnapshot] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def snapshot_count(self) -> int:
        return len(self.financial_statement_snapshots) + len(self.sap_score_snapshots)
