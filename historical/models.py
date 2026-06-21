from dataclasses import dataclass, field


@dataclass
class FinancialStatementSnapshot:
    symbol: str
    fiscal_year: int
    fiscal_quarter: int
    statement_date: str
    published_date: str
    snapshot_date: str
    source: str
    source_version: str
    is_point_in_time: bool
    created_at: str
    statement_type: str
    payload_json: str = "{}"
    warning: str = ""


@dataclass
class SAPScoreSnapshot:
    symbol: str
    fiscal_year: int
    fiscal_quarter: int
    statement_date: str
    published_date: str
    snapshot_date: str
    source: str
    source_version: str
    is_point_in_time: bool
    created_at: str
    sap_score: float | None = None
    piotroski_score: float | None = None
    data_quality_score: float | None = None
    credibility_grade: str = "D"
    warning: str = ""


@dataclass
class SnapshotMetadata:
    symbol: str
    fiscal_year: int
    fiscal_quarter: int
    statement_date: str
    published_date: str
    snapshot_date: str
    source: str
    source_version: str
    is_point_in_time: bool
    created_at: str
    metadata: dict = field(default_factory=dict)
    warning: str = ""
