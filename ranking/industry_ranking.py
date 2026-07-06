from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


UNKNOWN_INDUSTRY = "未知產業"
INSUFFICIENT = "資料不足"


@dataclass
class IndustryRankingResult:
    industry_name: str
    industry_size: int
    sap_rank: int | None
    trend_rank: int | None
    total_rank: int | None
    sap_percentile: float | None
    trend_percentile: float | None
    total_percentile: float | None
    top_percent: str
    industry_average_sap: float | None
    industry_average_trend: float | None
    industry_average_total: float | None
    summary_text: str

    @property
    def rating(self) -> str:
        if self.top_percent == "前 5%":
            return "★★★★★"
        if self.top_percent == "前 10%":
            return "★★★★★"
        if self.top_percent == "前 25%":
            return "★★★★"
        if self.top_percent == "前 50%":
            return "★★★"
        if self.top_percent == "後 50%":
            return "★★"
        return INSUFFICIENT

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["rating"] = self.rating
        return payload


class IndustryRankingEngine:
    def __init__(self, rows: Iterable[dict] | None = None):
        self.rows = [dict(row) for row in (rows or [])]

    def rank(self, target_symbol: str, rows: Iterable[dict] | None = None) -> IndustryRankingResult:
        source_rows = [dict(row) for row in (rows if rows is not None else self.rows)]
        target = self._find_target(source_rows, target_symbol)
        if target is None:
            return self._unknown_result()

        industry = self._industry_name(target)
        if self._is_unknown_industry(industry):
            return self._unknown_result()

        industry_rows = [
            row for row in source_rows
            if self._industry_name(row) == industry and self._is_success_row(row)
        ]
        if not industry_rows:
            return self._unknown_result(industry)

        sap_rank = self._rank_for(industry_rows, target, "sap")
        trend_rank = self._rank_for(industry_rows, target, "trend")
        total_rank = self._rank_for(industry_rows, target, "total")
        size = len(industry_rows)
        sap_percentile = self._percentile(sap_rank, size)
        trend_percentile = self._percentile(trend_rank, size)
        total_percentile = self._percentile(total_rank, size)
        top_percent = self._top_percent(total_percentile or sap_percentile)

        return IndustryRankingResult(
            industry_name=industry,
            industry_size=size,
            sap_rank=sap_rank,
            trend_rank=trend_rank,
            total_rank=total_rank,
            sap_percentile=sap_percentile,
            trend_percentile=trend_percentile,
            total_percentile=total_percentile,
            top_percent=top_percent,
            industry_average_sap=self._average_score(industry_rows, "sap"),
            industry_average_trend=self._average_score(industry_rows, "trend"),
            industry_average_total=self._average_score(industry_rows, "total"),
            summary_text=self._summary_text(top_percent),
        )

    def annotate_rows(self, rows: Iterable[dict] | None = None) -> list[dict]:
        source_rows = [dict(row) for row in (rows if rows is not None else self.rows)]
        annotated = []
        for row in source_rows:
            ranking = self.rank(str(row.get("symbol", "")), source_rows)
            updated = dict(row)
            updated.update(
                {
                    "industry_rank_label": ranking.top_percent,
                    "industry_size": ranking.industry_size,
                    "sap_rank": ranking.sap_rank or "",
                    "trend_rank": ranking.trend_rank or "",
                    "total_rank": ranking.total_rank or "",
                    "industry_average_sap": ranking.industry_average_sap or "",
                    "industry_average_trend": ranking.industry_average_trend or "",
                    "industry_average_total": ranking.industry_average_total or "",
                    "industry_ranking_summary": ranking.summary_text,
                }
            )
            annotated.append(updated)
        return annotated

    def _find_target(self, rows: list[dict], symbol: str) -> dict | None:
        normalized = self._normalize_symbol(symbol)
        for row in rows:
            if self._normalize_symbol(str(row.get("symbol", ""))) == normalized:
                return row
        return None

    def _industry_name(self, row: dict) -> str:
        industry = row.get("industry") or row.get("industry_name") or UNKNOWN_INDUSTRY
        return str(industry).strip() or UNKNOWN_INDUSTRY

    def _is_unknown_industry(self, industry: str) -> bool:
        return industry in {UNKNOWN_INDUSTRY, "-", INSUFFICIENT, "未知", "Unknown", "Unknown Industry"}

    def _is_success_row(self, row: dict) -> bool:
        status = str(row.get("status", "success")).lower()
        return status in {"", "success", "ok"}

    def _rank_for(self, rows: list[dict], target: dict, score_type: str) -> int | None:
        target_score = self._score(target, score_type)
        if target_score is None:
            return None

        scores = [score for score in (self._score(row, score_type) for row in rows) if score is not None]
        if not scores:
            return None
        return 1 + sum(1 for score in scores if score > target_score)

    def _score(self, row: dict, score_type: str) -> float | None:
        if score_type == "sap":
            return self._to_float(row.get("sap_score"))
        if score_type == "trend":
            return self._to_float(row.get("trend_score"))
        if score_type == "total":
            total = self._to_float(row.get("total_score"))
            if total is not None:
                return total
            sap = self._to_float(row.get("sap_score"))
            trend = self._to_float(row.get("trend_score"))
            if sap is None or trend is None:
                return None
            return round(sap * 0.6 + trend * 0.4, 2)
        return None

    def _average_score(self, rows: list[dict], score_type: str) -> float | None:
        scores = [score for score in (self._score(row, score_type) for row in rows) if score is not None]
        if not scores:
            return None
        return round(sum(scores) / len(scores), 2)

    def _percentile(self, rank: int | None, size: int) -> float | None:
        if rank is None or size <= 0:
            return None
        return round(rank / size * 100, 2)

    def _top_percent(self, percentile: float | None) -> str:
        if percentile is None:
            return INSUFFICIENT
        if percentile <= 5:
            return "前 5%"
        if percentile <= 10:
            return "前 10%"
        if percentile <= 25:
            return "前 25%"
        if percentile <= 50:
            return "前 50%"
        return "後 50%"

    def _summary_text(self, top_percent: str) -> str:
        if top_percent in {"前 5%", "前 10%"}:
            return f"產業排名屬{top_percent}，在同產業中屬於相對強勢公司。"
        if top_percent in {"前 25%", "前 50%"}:
            return f"產業排名屬{top_percent}，在同產業中具備一定相對優勢。"
        if top_percent == "後 50%":
            return "產業排名落後，建議優先研究同產業中排名更高的公司。"
        return "產業資料不足，暫無法排名"

    def _unknown_result(self, industry_name: str = UNKNOWN_INDUSTRY) -> IndustryRankingResult:
        return IndustryRankingResult(
            industry_name=industry_name or UNKNOWN_INDUSTRY,
            industry_size=0,
            sap_rank=None,
            trend_rank=None,
            total_rank=None,
            sap_percentile=None,
            trend_percentile=None,
            total_percentile=None,
            top_percent=INSUFFICIENT,
            industry_average_sap=None,
            industry_average_trend=None,
            industry_average_total=None,
            summary_text="產業資料不足，暫無法排名",
        )

    def _normalize_symbol(self, symbol: str) -> str:
        return symbol.strip().upper()

    def _to_float(self, value) -> float | None:
        if value in {None, ""}:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None


def load_analyzed_rows_from_csv(path: str | Path) -> list[dict]:
    csv_path = Path(path)
    if not csv_path.exists():
        return []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))
