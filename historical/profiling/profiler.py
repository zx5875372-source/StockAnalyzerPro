from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3

from historical.profiling.metrics import (
    calculate_missing_percentage,
    calculate_point_in_time_percentage,
    calculate_quality_score,
    count_duplicate_warnings,
    count_missing_field_errors,
)
from historical.profiling.profile_result import ProfileResult
from historical.repository import HistoricalSnapshotRepository
from importers.import_result import ImportResult


DEFAULT_DATA_QUALITY_REPORT_PATH = Path("reports/data_quality_report.md")


class HistoricalProfiler:
    def profile_import(self, import_result: ImportResult) -> ProfileResult:
        imported_rows = import_result.imported_count
        failed_rows = import_result.failed_count
        total_rows = imported_rows + failed_rows
        warning_rows = len(import_result.warnings)
        duplicate_rows = count_duplicate_warnings(import_result.warnings)
        missing_field_count = count_missing_field_errors(import_result.errors)
        point_in_time_count = sum(
            1
            for snapshot in [
                *import_result.sap_score_snapshots,
                *import_result.financial_statement_snapshots,
            ]
            if snapshot.is_point_in_time
        )

        return build_profile_result(
            total_rows=total_rows,
            imported_rows=imported_rows,
            failed_rows=failed_rows,
            warning_rows=warning_rows,
            duplicate_rows=duplicate_rows,
            missing_field_count=missing_field_count,
            point_in_time_count=point_in_time_count,
        )

    def profile_repository(self, repository: HistoricalSnapshotRepository) -> ProfileResult:
        rows = load_repository_rows(repository)
        total_rows = len(rows)
        warning_rows = sum(1 for row in rows if row.get("warning"))
        duplicate_rows = count_duplicate_repository_rows(rows)
        missing_field_count = count_missing_repository_fields(rows)
        point_in_time_count = sum(1 for row in rows if row["is_point_in_time"])

        return build_profile_result(
            total_rows=total_rows,
            imported_rows=total_rows,
            failed_rows=0,
            warning_rows=warning_rows,
            duplicate_rows=duplicate_rows,
            missing_field_count=missing_field_count,
            point_in_time_count=point_in_time_count,
        )


def build_profile_result(
    total_rows: int,
    imported_rows: int,
    failed_rows: int,
    warning_rows: int,
    duplicate_rows: int,
    missing_field_count: int,
    point_in_time_count: int,
) -> ProfileResult:
    return ProfileResult(
        total_rows=total_rows,
        imported_rows=imported_rows,
        failed_rows=failed_rows,
        warning_rows=warning_rows,
        duplicate_rows=duplicate_rows,
        missing_field_count=missing_field_count,
        missing_percentage=calculate_missing_percentage(missing_field_count, total_rows),
        point_in_time_count=point_in_time_count,
        point_in_time_percentage=calculate_point_in_time_percentage(point_in_time_count, imported_rows),
        quality_score=calculate_quality_score(
            failed_rows=failed_rows,
            missing_field_count=missing_field_count,
            duplicate_rows=duplicate_rows,
        ),
    )


def load_repository_rows(repository: HistoricalSnapshotRepository) -> list[dict]:
    with closing(sqlite3.connect(repository.db_path)) as connection:
        connection.row_factory = sqlite3.Row
        financial_rows = [
            dict(row)
            | {
                "table_name": "financial_statement_snapshots",
                "identity_type": row["statement_type"],
            }
            for row in connection.execute("SELECT * FROM financial_statement_snapshots").fetchall()
        ]
        sap_rows = [
            dict(row)
            | {
                "table_name": "sap_score_snapshots",
                "identity_type": "sap_score",
            }
            for row in connection.execute("SELECT * FROM sap_score_snapshots").fetchall()
        ]
    return financial_rows + sap_rows


def count_duplicate_repository_rows(rows: list[dict]) -> int:
    seen = set()
    duplicate_count = 0
    for row in rows:
        key = (
            row["table_name"],
            row["symbol"],
            row["fiscal_year"],
            row["fiscal_quarter"],
            row["snapshot_date"],
            row["source"],
            row["source_version"],
            row["identity_type"],
        )
        if key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
    return duplicate_count


def count_missing_repository_fields(rows: list[dict]) -> int:
    missing_count = 0
    for row in rows:
        required_fields = repository_required_fields(row["table_name"])
        for field_name in required_fields:
            value = row.get(field_name)
            if value is None or (isinstance(value, str) and not value.strip()):
                missing_count += 1
    return missing_count


def repository_required_fields(table_name: str) -> list[str]:
    fields = [
        "symbol",
        "fiscal_year",
        "fiscal_quarter",
        "statement_date",
        "published_date",
        "snapshot_date",
        "source",
        "source_version",
        "is_point_in_time",
        "created_at",
    ]
    if table_name == "financial_statement_snapshots":
        return fields + ["statement_type", "payload_json"]
    return fields + ["credibility_grade"]


def write_data_quality_report(
    profile: ProfileResult,
    output_path: str | Path = DEFAULT_DATA_QUALITY_REPORT_PATH,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_data_quality_report(profile), encoding="utf-8")


def format_data_quality_report(profile: ProfileResult) -> str:
    return f"""# Data Quality Report

| Metric | Value |
| --- | --- |
| Imported Rows | {profile.imported_rows} |
| Failed Rows | {profile.failed_rows} |
| Warnings | {profile.warning_rows} |
| Duplicates | {profile.duplicate_rows} |
| Missing % | {profile.missing_percentage:.2f}% |
| Point-in-Time % | {profile.point_in_time_percentage:.2f}% |
| Quality Score | {profile.quality_score:.2f} |
"""
