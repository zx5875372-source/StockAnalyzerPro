from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class QualificationResult:
    total_snapshots: int = 0
    financial_snapshot_count: int = 0
    sap_snapshot_count: int = 0
    point_in_time_count: int = 0
    research_only_count: int = 0
    missing_published_date_count: int = 0
    not_point_in_time_count: int = 0
    qualified_sap_snapshot_count: int = 0
    research_only_sap_snapshot_count: int = 0
    can_formal_backtest: bool = False
    warnings: list[str] = field(default_factory=list)
    disqualification_reasons: dict[str, int] = field(default_factory=dict)
