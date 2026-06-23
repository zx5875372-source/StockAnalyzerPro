from __future__ import annotations

from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.qualification.qualification_result import QualificationResult
from historical.repository import HistoricalSnapshotRepository


DEFAULT_QUALIFICATION_REPORT_PATH = Path("reports/historical_qualification_report.md")
DISQUALIFYING_WARNINGS = {
    "missing_published_date",
    "not_point_in_time",
}


class HistoricalQualifier:
    def qualify_repository(self, repository: HistoricalSnapshotRepository) -> QualificationResult:
        financial_snapshots = repository.list_financial_snapshots()
        sap_snapshots = repository.list_sap_snapshots()
        snapshots = [*financial_snapshots, *sap_snapshots]
        result = QualificationResult(
            total_snapshots=len(snapshots),
            financial_snapshot_count=len(financial_snapshots),
            sap_snapshot_count=len(sap_snapshots),
        )

        for snapshot in snapshots:
            reasons = disqualification_reasons(snapshot)
            if snapshot.is_point_in_time:
                result.point_in_time_count += 1
            else:
                result.not_point_in_time_count += 1
            if "missing_published_date" in reasons:
                result.missing_published_date_count += 1

            if reasons:
                result.research_only_count += 1
                for reason in reasons:
                    result.disqualification_reasons[reason] = result.disqualification_reasons.get(reason, 0) + 1
                result.warnings.append(
                    f"{snapshot.symbol} {snapshot.fiscal_year}Q{snapshot.fiscal_quarter}: research_only ({', '.join(reasons)})"
                )
                if isinstance(snapshot, SAPScoreSnapshot):
                    result.research_only_sap_snapshot_count += 1
                continue

            if isinstance(snapshot, SAPScoreSnapshot):
                result.qualified_sap_snapshot_count += 1

        result.can_formal_backtest = (
            result.sap_snapshot_count > 0
            and result.qualified_sap_snapshot_count == result.sap_snapshot_count
        )
        return result


def disqualification_reasons(snapshot: FinancialStatementSnapshot | SAPScoreSnapshot) -> list[str]:
    reasons = []
    if not snapshot.is_point_in_time:
        reasons.append("not_point_in_time")
    for warning in split_warnings(snapshot.warning):
        if warning in DISQUALIFYING_WARNINGS and warning not in reasons:
            reasons.append(warning)
    return reasons


def split_warnings(value: str) -> list[str]:
    warnings = []
    for chunk in str(value or "").replace(",", ";").split(";"):
        warning = chunk.strip()
        if warning:
            warnings.append(warning)
    return warnings


def write_qualification_report(
    result: QualificationResult,
    output_path: str | Path = DEFAULT_QUALIFICATION_REPORT_PATH,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(format_qualification_report(result), encoding="utf-8")


def format_qualification_report(result: QualificationResult) -> str:
    lines = [
        "# Historical Qualification Report",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Total Snapshots | {result.total_snapshots} |",
        f"| Financial Snapshots | {result.financial_snapshot_count} |",
        f"| SAP Snapshots | {result.sap_snapshot_count} |",
        f"| Point-in-Time Snapshots | {result.point_in_time_count} |",
        f"| Research-Only Snapshots | {result.research_only_count} |",
        f"| Missing Published Date | {result.missing_published_date_count} |",
        f"| Not Point-in-Time | {result.not_point_in_time_count} |",
        f"| Qualified SAP Snapshots | {result.qualified_sap_snapshot_count} |",
        f"| Research-Only SAP Snapshots | {result.research_only_sap_snapshot_count} |",
        f"| Can Formal Backtest | {str(result.can_formal_backtest).lower()} |",
        "",
        "## Disqualification Reasons",
        "",
    ]
    if result.disqualification_reasons:
        lines.extend(
            f"- {reason}: {count}"
            for reason, count in sorted(result.disqualification_reasons.items())
        )
    else:
        lines.append("- None")

    lines.extend(["", "## Warnings", ""])
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- None")
    return "\n".join(lines) + "\n"
