from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from historical.repository import HistoricalSnapshotRepository
from historical.validation import HistoricalValidator
from models.financial_data import FinancialData, FinancialPeriod
from modules.analyzer import analyze_stock


DEFAULT_SUMMARY_PATH = Path("reports/historical_generator_summary.md")
GENERATOR_SOURCE = "historical_sap_generator"
GENERATOR_VERSION = "v1"


PERIOD_FIELDS = {
    field_name
    for field_name in FinancialPeriod.__dataclass_fields__
    if field_name != "period"
}

FIELD_ALIASES = {
    "net_income": ["net_income", "netincome", "net_income_after_tax", "NetIncome"],
    "total_assets": ["total_assets", "totalassets", "TotalAssets"],
    "total_equity": ["total_equity", "totalequity", "TotalEquity"],
    "total_debt": ["total_debt", "totaldebt", "TotalDebt"],
    "long_term_debt": ["long_term_debt", "longtermdebt", "LongTermDebt"],
    "current_assets": ["current_assets", "currentassets", "CurrentAssets"],
    "current_liabilities": ["current_liabilities", "currentliabilities", "CurrentLiabilities"],
    "revenue": ["revenue", "Revenue"],
    "gross_profit": ["gross_profit", "grossprofit", "GrossProfit"],
    "operating_income": ["operating_income", "operatingincome", "OperatingIncome"],
    "operating_cashflow": ["operating_cashflow", "operatingcashflow", "OperatingCashFlow"],
    "free_cashflow": ["free_cashflow", "freecashflow", "FreeCashFlow"],
    "shares_outstanding": ["shares_outstanding", "sharesoutstanding", "SharesOutstanding"],
    "eps": ["eps", "EPS"],
    "book_value_per_share": ["book_value_per_share", "bookvaluepershare", "BookValuePerShare"],
}


@dataclass
class HistoricalSAPGenerationResult:
    generated: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    snapshots: list[SAPScoreSnapshot] = field(default_factory=list)
    affected_periods: list[str] = field(default_factory=list)
    generator_version: str = GENERATOR_VERSION


class HistoricalSAPGenerator:
    def __init__(
        self,
        repository: HistoricalSnapshotRepository | None = None,
        summary_path: str | Path = DEFAULT_SUMMARY_PATH,
    ):
        self.repository = repository
        self.summary_path = Path(summary_path)
        self.validator = HistoricalValidator()

    def generate_snapshot(self, financial_snapshot: FinancialStatementSnapshot) -> SAPScoreSnapshot:
        financial_data = build_financial_data(financial_snapshot)
        analysis = analyze_stock(financial_data)
        warning = build_warning(financial_snapshot, financial_data)

        return SAPScoreSnapshot(
            symbol=financial_snapshot.symbol,
            fiscal_year=financial_snapshot.fiscal_year,
            fiscal_quarter=financial_snapshot.fiscal_quarter,
            statement_date=financial_snapshot.statement_date,
            published_date=financial_snapshot.published_date,
            snapshot_date=financial_snapshot.snapshot_date,
            source=GENERATOR_SOURCE,
            source_version=GENERATOR_VERSION,
            is_point_in_time=financial_snapshot.is_point_in_time and not warning,
            created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            sap_score=to_number(analysis.get("sap_score")),
            piotroski_score=to_number((analysis.get("piotroski") or {}).get("score")),
            data_quality_score=calculate_data_quality_score(financial_data),
            credibility_grade=calculate_credibility_grade(
                to_number(analysis.get("sap_score")),
                financial_snapshot.is_point_in_time,
                warning,
            ),
            warning=warning,
        )

    def generate_all(
        self,
        repository: HistoricalSnapshotRepository | None = None,
    ) -> HistoricalSAPGenerationResult:
        active_repository = repository or self.repository
        if active_repository is None:
            raise ValueError("HistoricalSAPGenerator requires a repository for generate_all()")

        result = self.generate_snapshots(
            active_repository.list_financial_snapshots(),
            repository=active_repository,
            write_report=False,
        )
        write_summary(result, self.summary_path)
        return result

    def generate_snapshots(
        self,
        financial_snapshots: list[FinancialStatementSnapshot],
        repository: HistoricalSnapshotRepository | None = None,
        write_report: bool = True,
    ) -> HistoricalSAPGenerationResult:
        active_repository = repository or self.repository
        if active_repository is None:
            raise ValueError("HistoricalSAPGenerator requires a repository for generate_snapshots()")

        result = HistoricalSAPGenerationResult()
        for financial_snapshot in financial_snapshots:
            try:
                sap_snapshot = self.generate_snapshot(financial_snapshot)
                validation = self.validator.validate_sap_snapshot(sap_snapshot)
                if not validation.is_valid:
                    result.failed += 1
                    result.errors.extend(
                        f"{sap_snapshot.symbol} {sap_snapshot.fiscal_year}Q{sap_snapshot.fiscal_quarter}: {error}"
                        for error in validation.errors
                    )
                    continue

                status = active_repository.insert_sap_snapshot(sap_snapshot)
                if status == "updated":
                    result.updated += 1
                else:
                    result.generated += 1
                result.warnings.extend(
                    f"{sap_snapshot.symbol} {sap_snapshot.fiscal_year}Q{sap_snapshot.fiscal_quarter}: {warning}"
                    for warning in validation.warnings
                )
                result.snapshots.append(sap_snapshot)
            except Exception as error:
                result.failed += 1
                result.errors.append(
                    f"{financial_snapshot.symbol} {financial_snapshot.fiscal_year}Q{financial_snapshot.fiscal_quarter}: {error}"
                )

        if write_report:
            write_summary(result, self.summary_path)
        return result

    def generate_incremental(
        self,
        financial_snapshots: list[FinancialStatementSnapshot] | None = None,
        repository: HistoricalSnapshotRepository | None = None,
        write_report: bool = True,
    ) -> HistoricalSAPGenerationResult:
        active_repository = repository or self.repository
        if active_repository is None:
            raise ValueError("HistoricalSAPGenerator requires a repository for generate_incremental()")

        snapshots = financial_snapshots
        if snapshots is None:
            snapshots = active_repository.list_financial_snapshots()

        affected_snapshots = []
        result = HistoricalSAPGenerationResult()
        for financial_snapshot in snapshots:
            existing = active_repository.get_latest_sap_snapshot_for_period(
                financial_snapshot.symbol,
                financial_snapshot.fiscal_year,
                financial_snapshot.fiscal_quarter,
            )
            reason = incremental_rebuild_reason(financial_snapshot, existing)
            period_key = format_period_key(financial_snapshot)
            if reason is None:
                result.skipped += 1
                continue
            result.affected_periods.append(f"{period_key}: {reason}")
            if reason == "publication_timeline_changed":
                result.warnings.append(
                    f"{period_key}: publication_timeline_changed "
                    f"{existing.published_date}->{financial_snapshot.published_date}, "
                    f"{existing.snapshot_date}->{financial_snapshot.snapshot_date}"
                )
            affected_snapshots.append(financial_snapshot)

        generated = self.generate_snapshots(
            affected_snapshots,
            repository=active_repository,
            write_report=False,
        )
        result.generated += generated.generated
        result.updated += generated.updated
        result.failed += generated.failed
        result.warnings.extend(generated.warnings)
        result.errors.extend(generated.errors)
        result.snapshots.extend(generated.snapshots)

        if write_report:
            write_summary(result, self.summary_path)
        return result


def build_financial_data(snapshot: FinancialStatementSnapshot) -> FinancialData:
    payload = parse_payload(snapshot.payload_json)
    current_payload = payload.get("current") if isinstance(payload.get("current"), dict) else payload
    previous_payload = payload.get("previous") if isinstance(payload.get("previous"), dict) else None
    current_period = build_period(current_payload, period=snapshot.statement_date)
    previous_period = build_period(previous_payload, period=None) if previous_payload else None
    missing_fields = [
        field_name
        for field_name in PERIOD_FIELDS
        if getattr(current_period, field_name) is None
    ]

    return FinancialData(
        symbol=snapshot.symbol,
        company_name=payload.get("company_name"),
        industry=payload.get("industry"),
        sector=payload.get("sector"),
        price=to_number(payload.get("price")),
        pe=to_number(payload.get("pe")),
        pb=to_number(payload.get("pb")),
        current=current_period,
        previous=previous_period,
        missing_fields=missing_fields,
        diagnostics=[],
    )


def parse_payload(payload_json: str) -> dict:
    if not payload_json:
        return {}
    payload = json.loads(payload_json)
    if not isinstance(payload, dict):
        raise ValueError("FinancialStatementSnapshot.payload_json must be a JSON object")
    return payload


def build_period(payload: dict | None, period: str | None) -> FinancialPeriod:
    values = {"period": period}
    payload = payload or {}
    for field_name in PERIOD_FIELDS:
        values[field_name] = find_number(payload, field_name)
    return FinancialPeriod(**values)


def find_number(payload: dict, field_name: str) -> float | None:
    normalized_payload = {normalize_key(key): value for key, value in payload.items()}
    for alias in FIELD_ALIASES.get(field_name, [field_name]):
        value = payload.get(alias)
        if value is None:
            value = normalized_payload.get(normalize_key(alias))
        number = to_number(value)
        if number is not None:
            return number
    return None


def normalize_key(value: str) -> str:
    return str(value).replace(" ", "").replace("_", "").lower()


def to_number(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_data_quality_score(financial_data: FinancialData) -> int:
    return max(100 - len(financial_data.missing_fields) * 5, 0)


def build_warning(snapshot: FinancialStatementSnapshot, financial_data: FinancialData) -> str:
    warnings = []
    if snapshot.warning:
        warnings.append(snapshot.warning)
    if not snapshot.is_point_in_time:
        warnings.append("not_point_in_time")
    if financial_data.missing_fields:
        warnings.append(f"missing_fields:{','.join(financial_data.missing_fields)}")
    return ";".join(deduplicate(warnings))


def deduplicate(values: list[str]) -> list[str]:
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result


def calculate_credibility_grade(
    sap_score: float | None,
    is_point_in_time: bool,
    warning: str,
) -> str:
    if not is_point_in_time or warning:
        return "C"
    if sap_score is None:
        return "D"
    if sap_score >= 80:
        return "A"
    if sap_score >= 60:
        return "B"
    return "C"


def incremental_rebuild_reason(
    financial_snapshot: FinancialStatementSnapshot,
    existing_snapshot: SAPScoreSnapshot | None,
) -> str | None:
    if existing_snapshot is None:
        return "missing_sap_snapshot"
    if existing_snapshot.source_version != GENERATOR_VERSION:
        return "generator_version_changed"
    if (
        existing_snapshot.published_date != financial_snapshot.published_date
        or existing_snapshot.snapshot_date != financial_snapshot.snapshot_date
    ):
        return "publication_timeline_changed"
    return None


def format_period_key(snapshot: FinancialStatementSnapshot) -> str:
    return f"{snapshot.symbol} {snapshot.fiscal_year}Q{snapshot.fiscal_quarter}"


def write_summary(result: HistoricalSAPGenerationResult, summary_path: Path) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Historical Generator Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Generator Version | {result.generator_version} |",
        f"| Generated | {result.generated} |",
        f"| Updated | {result.updated} |",
        f"| Skipped | {result.skipped} |",
        f"| Failed | {result.failed} |",
        f"| Warnings | {len(result.warnings)} |",
        "",
        "## Affected Periods",
        "",
    ]
    if result.affected_periods:
        lines.extend(f"- {period}" for period in result.affected_periods)
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Warning Details",
        "",
    ])
    if result.warnings:
        lines.extend(f"- {warning}" for warning in result.warnings)
    else:
        lines.append("- None")

    lines.extend(["", "## Errors", ""])
    if result.errors:
        lines.extend(f"- {error}" for error in result.errors)
    else:
        lines.append("- None")

    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
