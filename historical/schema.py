FINANCIAL_STATEMENT_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS financial_statement_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    statement_date TEXT NOT NULL,
    published_date TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    source TEXT NOT NULL,
    source_version TEXT NOT NULL,
    is_point_in_time INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    statement_type TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    warning TEXT
);
"""

SAP_SCORE_SNAPSHOTS_TABLE = """
CREATE TABLE IF NOT EXISTS sap_score_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    statement_date TEXT NOT NULL,
    published_date TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    source TEXT NOT NULL,
    source_version TEXT NOT NULL,
    is_point_in_time INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    sap_score REAL,
    piotroski_score REAL,
    data_quality_score REAL,
    credibility_grade TEXT NOT NULL,
    warning TEXT,
    UNIQUE(symbol, fiscal_year, fiscal_quarter, snapshot_date, source, source_version)
);
"""

SNAPSHOT_METADATA_TABLE = """
CREATE TABLE IF NOT EXISTS snapshot_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_quarter INTEGER NOT NULL,
    statement_date TEXT NOT NULL,
    published_date TEXT NOT NULL,
    snapshot_date TEXT NOT NULL,
    source TEXT NOT NULL,
    source_version TEXT NOT NULL,
    is_point_in_time INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL,
    warning TEXT
);
"""

HISTORICAL_SNAPSHOT_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_financial_statement_snapshots_lookup
ON financial_statement_snapshots (symbol, fiscal_year, fiscal_quarter, snapshot_date);

CREATE INDEX IF NOT EXISTS idx_sap_score_snapshots_lookup
ON sap_score_snapshots (symbol, snapshot_date, is_point_in_time);

CREATE INDEX IF NOT EXISTS idx_snapshot_metadata_lookup
ON snapshot_metadata (symbol, snapshot_date, source);
"""

HISTORICAL_SNAPSHOT_SCHEMA = "\n".join(
    [
        FINANCIAL_STATEMENT_SNAPSHOTS_TABLE,
        SAP_SCORE_SNAPSHOTS_TABLE,
        SNAPSHOT_METADATA_TABLE,
        HISTORICAL_SNAPSHOT_INDEXES,
    ]
)
