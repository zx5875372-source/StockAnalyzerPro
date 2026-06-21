from __future__ import annotations

from datetime import date

from historical.validation.validation_result import ValidationResult


VALID_CREDIBILITY_GRADES = {"A", "B", "C", "D"}


def require_present(result: ValidationResult, field_name: str, value) -> bool:
    result.field_count += 1
    if value is None:
        result.add_missing_field(field_name)
        return False
    if isinstance(value, str) and not value.strip():
        result.add_missing_field(field_name)
        return False
    return True


def validate_symbol(result: ValidationResult, symbol: str | None) -> None:
    if not require_present(result, "symbol", symbol):
        return
    if not isinstance(symbol, str):
        result.add_error("symbol must be a string")


def validate_iso_date(result: ValidationResult, field_name: str, value: str | None) -> date | None:
    if not require_present(result, field_name, value):
        return None
    date_text = str(value)
    if len(date_text) != 10 or date_text[4] != "-" or date_text[7] != "-":
        result.add_error(f"{field_name} must be an ISO date: {value}")
        return None
    try:
        return date.fromisoformat(date_text)
    except ValueError:
        result.add_error(f"{field_name} must be an ISO date: {value}")
        return None


def validate_fiscal_year(result: ValidationResult, fiscal_year) -> None:
    if not require_present(result, "fiscal_year", fiscal_year):
        return
    if not isinstance(fiscal_year, int) or fiscal_year < 1900:
        result.add_error(f"fiscal_year must be an integer >= 1900: {fiscal_year}")


def validate_fiscal_quarter(result: ValidationResult, fiscal_quarter) -> None:
    if not require_present(result, "fiscal_quarter", fiscal_quarter):
        return
    if not isinstance(fiscal_quarter, int) or fiscal_quarter not in {1, 2, 3, 4}:
        result.add_error(f"fiscal_quarter must be 1, 2, 3, or 4: {fiscal_quarter}")


def validate_score_range(
    result: ValidationResult,
    field_name: str,
    value,
    minimum: float,
    maximum: float,
) -> None:
    if not require_present(result, field_name, value):
        return
    if not isinstance(value, (int, float)):
        result.add_error(f"{field_name} must be numeric: {value}")
        return
    if value < minimum or value > maximum:
        result.add_error(f"{field_name} must be between {minimum:g} and {maximum:g}: {value}")


def validate_credibility_grade(result: ValidationResult, credibility_grade: str | None) -> None:
    if not require_present(result, "credibility_grade", credibility_grade):
        return
    if str(credibility_grade).upper() not in VALID_CREDIBILITY_GRADES:
        result.add_error(f"credibility_grade must be one of A, B, C, D: {credibility_grade}")


def validate_is_point_in_time(result: ValidationResult, is_point_in_time) -> None:
    if not require_present(result, "is_point_in_time", is_point_in_time):
        return
    if not isinstance(is_point_in_time, bool):
        result.add_error(f"is_point_in_time must be bool: {is_point_in_time}")


def validate_date_order(
    result: ValidationResult,
    published_date: date | None,
    snapshot_date: date | None,
) -> None:
    if published_date is not None and snapshot_date is not None and published_date > snapshot_date:
        result.add_error("published_date must be on or before snapshot_date")
