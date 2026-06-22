from __future__ import annotations


FAILED_ROW_PENALTY = 10
MISSING_FIELD_PENALTY = 2
DUPLICATE_ROW_PENALTY = 5


def calculate_percentage(count: int, total: int) -> float:
    if total <= 0:
        return 0.0
    return round((count / total) * 100, 2)


def calculate_missing_percentage(missing_field_count: int, total_rows: int) -> float:
    return calculate_percentage(missing_field_count, total_rows)


def calculate_point_in_time_percentage(point_in_time_count: int, total_rows: int) -> float:
    return calculate_percentage(point_in_time_count, total_rows)


def calculate_quality_score(
    failed_rows: int,
    missing_field_count: int,
    duplicate_rows: int,
) -> float:
    failed_penalty = failed_rows * FAILED_ROW_PENALTY
    missing_penalty = missing_field_count * MISSING_FIELD_PENALTY
    duplicate_penalty = duplicate_rows * DUPLICATE_ROW_PENALTY
    return max(100.0 - failed_penalty - missing_penalty - duplicate_penalty, 0.0)


def count_missing_field_errors(errors: list[str]) -> int:
    return sum(1 for error in errors if "Missing required field:" in error)


def count_duplicate_warnings(warnings: list[str]) -> int:
    return sum(1 for warning in warnings if "Duplicate historical snapshot key" in warning)
