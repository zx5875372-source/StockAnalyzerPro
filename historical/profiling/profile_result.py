from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProfileResult:
    total_rows: int = 0
    imported_rows: int = 0
    failed_rows: int = 0
    warning_rows: int = 0
    duplicate_rows: int = 0
    missing_field_count: int = 0
    missing_percentage: float = 0.0
    point_in_time_count: int = 0
    point_in_time_percentage: float = 0.0
    quality_score: float = 100.0
