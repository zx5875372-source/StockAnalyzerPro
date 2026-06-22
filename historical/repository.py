from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import sqlite3

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.schema import HISTORICAL_SNAPSHOT_SCHEMA


DEFAULT_DB_PATH = Path("historical_snapshots.db")


class HistoricalSnapshotRepository:
    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize_schema()

    def initialize_schema(self) -> None:
        with self._connect() as connection:
            connection.executescript(HISTORICAL_SNAPSHOT_SCHEMA)

    def insert_financial_snapshot(self, snapshot: FinancialStatementSnapshot) -> None:
        payload = asdict(snapshot)
        payload["is_point_in_time"] = int(snapshot.is_point_in_time)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO financial_statement_snapshots (
                    symbol,
                    fiscal_year,
                    fiscal_quarter,
                    statement_date,
                    published_date,
                    snapshot_date,
                    source,
                    source_version,
                    is_point_in_time,
                    created_at,
                    statement_type,
                    payload_json,
                    warning
                )
                VALUES (
                    :symbol,
                    :fiscal_year,
                    :fiscal_quarter,
                    :statement_date,
                    :published_date,
                    :snapshot_date,
                    :source,
                    :source_version,
                    :is_point_in_time,
                    :created_at,
                    :statement_type,
                    :payload_json,
                    :warning
                )
                """,
                payload,
            )

    def insert_sap_snapshot(self, snapshot: SAPScoreSnapshot) -> str:
        payload = asdict(snapshot)
        payload["is_point_in_time"] = int(snapshot.is_point_in_time)
        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT id
                FROM sap_score_snapshots
                WHERE symbol = ?
                  AND fiscal_year = ?
                  AND fiscal_quarter = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (snapshot.symbol, snapshot.fiscal_year, snapshot.fiscal_quarter),
            ).fetchone()
            if existing is not None:
                payload["id"] = existing["id"]
                connection.execute(
                    """
                    UPDATE sap_score_snapshots
                    SET
                        statement_date = :statement_date,
                        published_date = :published_date,
                        snapshot_date = :snapshot_date,
                        source = :source,
                        source_version = :source_version,
                        is_point_in_time = :is_point_in_time,
                        created_at = :created_at,
                        sap_score = :sap_score,
                        piotroski_score = :piotroski_score,
                        data_quality_score = :data_quality_score,
                        credibility_grade = :credibility_grade,
                        warning = :warning
                    WHERE id = :id
                    """,
                    payload,
                )
                return "updated"

            connection.execute(
                """
                INSERT INTO sap_score_snapshots (
                    symbol,
                    fiscal_year,
                    fiscal_quarter,
                    statement_date,
                    published_date,
                    snapshot_date,
                    source,
                    source_version,
                    is_point_in_time,
                    created_at,
                    sap_score,
                    piotroski_score,
                    data_quality_score,
                    credibility_grade,
                    warning
                )
                VALUES (
                    :symbol,
                    :fiscal_year,
                    :fiscal_quarter,
                    :statement_date,
                    :published_date,
                    :snapshot_date,
                    :source,
                    :source_version,
                    :is_point_in_time,
                    :created_at,
                    :sap_score,
                    :piotroski_score,
                    :data_quality_score,
                    :credibility_grade,
                    :warning
                )
                """,
                payload,
            )
            return "generated"

    def get_financial_snapshot(
        self,
        symbol: str,
        fiscal_year: int,
        fiscal_quarter: int,
        snapshot_date: str,
        statement_type: str | None = None,
    ) -> FinancialStatementSnapshot | None:
        query = """
            SELECT *
            FROM financial_statement_snapshots
            WHERE symbol = ?
              AND fiscal_year = ?
              AND fiscal_quarter = ?
              AND snapshot_date = ?
        """
        params = [symbol, fiscal_year, fiscal_quarter, snapshot_date]
        if statement_type is not None:
            query += " AND statement_type = ?"
            params.append(statement_type)
        query += " ORDER BY id DESC LIMIT 1"

        with self._connect() as connection:
            row = connection.execute(query, params).fetchone()
        if row is None:
            return None
        return financial_snapshot_from_row(row)

    def get_sap_snapshot(
        self,
        symbol: str,
        fiscal_year: int,
        fiscal_quarter: int,
        snapshot_date: str,
    ) -> SAPScoreSnapshot | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM sap_score_snapshots
                WHERE symbol = ?
                  AND fiscal_year = ?
                  AND fiscal_quarter = ?
                  AND snapshot_date = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (symbol, fiscal_year, fiscal_quarter, snapshot_date),
            ).fetchone()
        if row is None:
            return None
        return sap_snapshot_from_row(row)

    def list_snapshot_dates(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT snapshot_date FROM financial_statement_snapshots
                UNION
                SELECT snapshot_date FROM sap_score_snapshots
                ORDER BY snapshot_date
                """
            ).fetchall()
        return [row["snapshot_date"] for row in rows]

    def list_symbols(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT symbol FROM financial_statement_snapshots
                UNION
                SELECT symbol FROM sap_score_snapshots
                ORDER BY symbol
                """
            ).fetchall()
        return [row["symbol"] for row in rows]

    def list_financial_snapshots(self) -> list[FinancialStatementSnapshot]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM financial_statement_snapshots
                ORDER BY symbol, fiscal_year, fiscal_quarter, snapshot_date, id
                """
            ).fetchall()
        return [financial_snapshot_from_row(row) for row in rows]

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()


def financial_snapshot_from_row(row: sqlite3.Row) -> FinancialStatementSnapshot:
    return FinancialStatementSnapshot(
        symbol=row["symbol"],
        fiscal_year=row["fiscal_year"],
        fiscal_quarter=row["fiscal_quarter"],
        statement_date=row["statement_date"],
        published_date=row["published_date"],
        snapshot_date=row["snapshot_date"],
        source=row["source"],
        source_version=row["source_version"],
        is_point_in_time=bool(row["is_point_in_time"]),
        created_at=row["created_at"],
        statement_type=row["statement_type"],
        payload_json=row["payload_json"],
        warning=row["warning"] or "",
    )


def sap_snapshot_from_row(row: sqlite3.Row) -> SAPScoreSnapshot:
    return SAPScoreSnapshot(
        symbol=row["symbol"],
        fiscal_year=row["fiscal_year"],
        fiscal_quarter=row["fiscal_quarter"],
        statement_date=row["statement_date"],
        published_date=row["published_date"],
        snapshot_date=row["snapshot_date"],
        source=row["source"],
        source_version=row["source_version"],
        is_point_in_time=bool(row["is_point_in_time"]),
        created_at=row["created_at"],
        sap_score=row["sap_score"],
        piotroski_score=row["piotroski_score"],
        data_quality_score=row["data_quality_score"],
        credibility_grade=row["credibility_grade"],
        warning=row["warning"] or "",
    )
