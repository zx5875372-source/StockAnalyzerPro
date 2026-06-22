from __future__ import annotations

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.validation.rules import (
    require_present,
    validate_credibility_grade,
    validate_date_order,
    validate_fiscal_quarter,
    validate_fiscal_year,
    validate_iso_date,
    validate_is_point_in_time,
    validate_score_range,
    validate_symbol,
)
from historical.validation.validation_result import ValidationResult


MISSING_PUBLISHED_DATE_WARNING = "missing_published_date"


class HistoricalValidator:
    def __init__(self):
        self._seen_keys: set[tuple] = set()

    def validate_financial_snapshot(self, snapshot: FinancialStatementSnapshot) -> ValidationResult:
        result = ValidationResult()
        self._validate_common_fields(result, snapshot)
        require_present(result, "statement_type", snapshot.statement_type)
        self._warn_duplicate(result, snapshot)
        return result

    def validate_sap_snapshot(self, snapshot: SAPScoreSnapshot) -> ValidationResult:
        result = ValidationResult()
        self._validate_common_fields(result, snapshot)
        validate_score_range(result, "sap_score", snapshot.sap_score, 0, 100)
        validate_score_range(result, "piotroski_score", snapshot.piotroski_score, 0, 9)
        validate_score_range(result, "data_quality_score", snapshot.data_quality_score, 0, 100)
        validate_credibility_grade(result, snapshot.credibility_grade)
        self._warn_duplicate(result, snapshot)
        return result

    def _validate_common_fields(
        self,
        result: ValidationResult,
        snapshot: FinancialStatementSnapshot | SAPScoreSnapshot,
    ) -> None:
        validate_symbol(result, snapshot.symbol)
        published_date = validate_iso_date(result, "published_date", snapshot.published_date)
        snapshot_date = validate_iso_date(result, "snapshot_date", snapshot.snapshot_date)
        validate_date_order(result, published_date, snapshot_date)
        validate_fiscal_year(result, snapshot.fiscal_year)
        validate_fiscal_quarter(result, snapshot.fiscal_quarter)
        validate_is_point_in_time(result, snapshot.is_point_in_time)
        self._warn_missing_published_date_fallback(result, snapshot)

    def _warn_duplicate(
        self,
        result: ValidationResult,
        snapshot: FinancialStatementSnapshot | SAPScoreSnapshot,
    ) -> None:
        key = snapshot_identity(snapshot)
        if key in self._seen_keys:
            result.add_warning(f"Duplicate historical snapshot key: {key}")
            return
        self._seen_keys.add(key)

    def _warn_missing_published_date_fallback(
        self,
        result: ValidationResult,
        snapshot: FinancialStatementSnapshot | SAPScoreSnapshot,
    ) -> None:
        warnings = {item.strip() for item in str(snapshot.warning or "").split(",")}
        if MISSING_PUBLISHED_DATE_WARNING not in warnings:
            return
        if snapshot.is_point_in_time:
            result.add_error(
                f"{MISSING_PUBLISHED_DATE_WARNING} snapshots cannot be marked as point-in-time"
            )
            return
        result.add_warning(
            f"{MISSING_PUBLISHED_DATE_WARNING}: fallback published_date uses statement_date/date; not point-in-time"
        )


def snapshot_identity(snapshot: FinancialStatementSnapshot | SAPScoreSnapshot) -> tuple:
    return (
        snapshot.symbol,
        snapshot.fiscal_year,
        snapshot.fiscal_quarter,
        snapshot.snapshot_date,
        snapshot.source,
        snapshot.source_version,
    )
