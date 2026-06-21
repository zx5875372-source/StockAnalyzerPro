from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import sqlite3
from typing import Callable

from historical.models import SAPScoreSnapshot
from historical.repository import HistoricalSnapshotRepository
from modules.downloader import normalize_symbol


CURRENT_ANALYSIS_PROXY_SOURCE = "current_analysis_proxy"
CURRENT_ANALYSIS_PROXY_VERSION = "v0"
NOT_POINT_IN_TIME_WARNING = "not_point_in_time"


@dataclass
class SnapshotGenerationFailure:
    symbol: str
    error: str


@dataclass
class SnapshotGenerationResult:
    snapshot_date: str
    total_count: int
    inserted_count: int = 0
    skipped_existing_count: int = 0
    failed_count: int = 0
    snapshots: list[SAPScoreSnapshot] = field(default_factory=list)
    failures: list[SnapshotGenerationFailure] = field(default_factory=list)


class SnapshotGenerator:
    def __init__(
        self,
        repository: HistoricalSnapshotRepository,
        scan_func: Callable[[dict], dict] | None = None,
    ):
        self.repository = repository
        self.scan_func = scan_func

    def generate(
        self,
        stocks: list[dict],
        snapshot_date: str | None = None,
        verbose: bool = True,
    ) -> SnapshotGenerationResult:
        resolved_snapshot_date = snapshot_date or date.today().isoformat()
        created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        result = SnapshotGenerationResult(
            snapshot_date=resolved_snapshot_date,
            total_count=len(stocks),
        )

        for index, stock in enumerate(stocks, start=1):
            symbol = normalize_symbol(str(stock["symbol"]))
            if verbose:
                print(f"[{index}/{len(stocks)}] 建立 repository snapshot {symbol} {stock.get('name', '')}")

            analysis = self._scan(stock)
            if analysis.get("status") != "success":
                result.failed_count += 1
                result.failures.append(
                    SnapshotGenerationFailure(
                        symbol=symbol,
                        error=str(analysis.get("error") or "analysis failed"),
                    )
                )
                continue

            snapshot = build_sap_score_snapshot(
                stock=stock,
                analysis=analysis,
                snapshot_date=resolved_snapshot_date,
                created_at=created_at,
            )
            try:
                self.repository.insert_sap_snapshot(snapshot)
            except sqlite3.IntegrityError as error:
                if "UNIQUE constraint failed" not in str(error):
                    raise
                result.skipped_existing_count += 1
                continue

            result.inserted_count += 1
            result.snapshots.append(snapshot)

        return result

    def _scan(self, stock: dict) -> dict:
        if self.scan_func is None:
            from scan import scan_stock

            return scan_stock(stock)
        return self.scan_func(stock)


def build_sap_score_snapshot(
    stock: dict,
    analysis: dict,
    snapshot_date: str,
    created_at: str,
) -> SAPScoreSnapshot:
    year, quarter = fiscal_period_from_snapshot_date(snapshot_date)
    symbol = normalize_symbol(str(analysis.get("symbol") or stock["symbol"]))

    return SAPScoreSnapshot(
        symbol=symbol,
        fiscal_year=year,
        fiscal_quarter=quarter,
        statement_date=snapshot_date,
        published_date=snapshot_date,
        snapshot_date=snapshot_date,
        source=CURRENT_ANALYSIS_PROXY_SOURCE,
        source_version=CURRENT_ANALYSIS_PROXY_VERSION,
        is_point_in_time=False,
        created_at=created_at,
        sap_score=_numeric_or_none(analysis.get("sap_score")),
        piotroski_score=_numeric_or_none(analysis.get("piotroski_score")),
        data_quality_score=_numeric_or_none(analysis.get("data_quality_score")),
        credibility_grade="C",
        warning=NOT_POINT_IN_TIME_WARNING,
    )


def fiscal_period_from_snapshot_date(snapshot_date: str) -> tuple[int, int]:
    parsed_date = date.fromisoformat(snapshot_date)
    quarter = ((parsed_date.month - 1) // 3) + 1
    return parsed_date.year, quarter


def _numeric_or_none(value):
    if isinstance(value, (int, float)):
        return value
    return None
