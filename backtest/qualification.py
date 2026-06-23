from __future__ import annotations

from historical.qualification import HistoricalQualifier
from historical.qualification.qualification_result import QualificationResult
from historical.repository import HistoricalSnapshotRepository


RESEARCH_ONLY_BACKTEST_NOTICE = "此回測僅供研究與系統驗證，不可視為正式 point-in-time 投資績效。"


def qualify_repository_for_backtest(repository: HistoricalSnapshotRepository) -> dict:
    return qualification_to_summary(HistoricalQualifier().qualify_repository(repository))


def csv_qualification_summary() -> dict:
    return {
        "qualification_grade": "N/A",
        "qualification_reason": "CSV snapshot source uses existing credibility logic.",
        "research_only_count": 0,
        "point_in_time_count": 0,
        "missing_published_date_count": 0,
        "not_point_in_time_count": 0,
        "is_formal_point_in_time": False,
        "qualification_notice": "",
    }


def qualification_to_summary(result: QualificationResult) -> dict:
    if result.can_formal_backtest and result.research_only_count == 0:
        grade = "A"
        reason = "All repository SAP snapshots are point-in-time qualified."
        notice = ""
    elif result.research_only_count > 0:
        grade = "C"
        reason = "Repository contains research-only snapshots."
        notice = RESEARCH_ONLY_BACKTEST_NOTICE
    else:
        grade = "D"
        reason = "Repository does not contain qualified SAP snapshots for formal validation."
        notice = RESEARCH_ONLY_BACKTEST_NOTICE

    return {
        "qualification_grade": grade,
        "qualification_reason": reason,
        "research_only_count": result.research_only_count,
        "point_in_time_count": result.point_in_time_count,
        "missing_published_date_count": result.missing_published_date_count,
        "not_point_in_time_count": result.not_point_in_time_count,
        "is_formal_point_in_time": result.can_formal_backtest and result.research_only_count == 0,
        "qualification_notice": notice,
    }
