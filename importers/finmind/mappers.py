from __future__ import annotations

from datetime import date
import json

from historical.models import FinancialStatementSnapshot, SAPScoreSnapshot
from modules.downloader import normalize_symbol


FINMIND_SOURCE = "finmind"
FINMIND_SOURCE_VERSION = "v1"


class FinMindMappingError(ValueError):
    pass


def map_financial_statement_row(row: dict) -> FinancialStatementSnapshot:
    symbol = normalize_symbol(str(required_value(row, "symbol", "stock_id")))
    statement_date = parse_date(required_value(row, "statement_date", "date"))
    fiscal_year = parse_year(row.get("fiscal_year") or row.get("year"), default_year=statement_date.year)
    fiscal_quarter = parse_quarter(row.get("fiscal_quarter") or row.get("quarter"), statement_date=statement_date)
    published_date = parse_date(required_value(row, "published_date", "release_date", "filing_date"))
    snapshot_date = parse_date(row.get("snapshot_date") or published_date.isoformat())
    statement_type = str(required_value(row, "statement_type", "type"))

    return FinancialStatementSnapshot(
        symbol=symbol,
        fiscal_year=fiscal_year,
        fiscal_quarter=fiscal_quarter,
        statement_date=statement_date.isoformat(),
        published_date=published_date.isoformat(),
        snapshot_date=snapshot_date.isoformat(),
        source=FINMIND_SOURCE,
        source_version=FINMIND_SOURCE_VERSION,
        is_point_in_time=True,
        created_at=str(row.get("created_at") or ""),
        statement_type=statement_type,
        payload_json=build_payload_json(row),
        warning=str(row.get("warning") or ""),
    )


def map_sap_snapshot_row(row: dict) -> SAPScoreSnapshot:
    symbol = normalize_symbol(str(required_value(row, "symbol", "stock_id")))
    statement_date = parse_date(required_value(row, "statement_date", "date"))
    fiscal_year = parse_year(row.get("fiscal_year") or row.get("year"), default_year=statement_date.year)
    fiscal_quarter = parse_quarter(row.get("fiscal_quarter") or row.get("quarter"), statement_date=statement_date)
    published_date = parse_date(required_value(row, "published_date", "release_date", "filing_date"))
    snapshot_date = parse_date(row.get("snapshot_date") or published_date.isoformat())

    return SAPScoreSnapshot(
        symbol=symbol,
        fiscal_year=fiscal_year,
        fiscal_quarter=fiscal_quarter,
        statement_date=statement_date.isoformat(),
        published_date=published_date.isoformat(),
        snapshot_date=snapshot_date.isoformat(),
        source=FINMIND_SOURCE,
        source_version=FINMIND_SOURCE_VERSION,
        is_point_in_time=True,
        created_at=str(row.get("created_at") or ""),
        sap_score=parse_optional_float(required_value(row, "sap_score")),
        piotroski_score=parse_optional_float(required_value(row, "piotroski_score")),
        data_quality_score=parse_optional_float(required_value(row, "data_quality_score")),
        credibility_grade=str(required_value(row, "credibility_grade")),
        warning=str(row.get("warning") or ""),
    )


def required_value(row: dict, *field_names: str):
    for field_name in field_names:
        value = row.get(field_name)
        if value is not None and not (isinstance(value, str) and not value.strip()):
            return value
    names = ", ".join(field_names)
    raise FinMindMappingError(f"Missing required FinMind field: {names}")


def parse_year(value, default_year: int | None = None) -> int:
    if value is None or value == "":
        if default_year is None:
            raise FinMindMappingError("Missing required FinMind field: fiscal_year")
        return default_year

    year = int(value)
    if 1 <= year <= 199:
        return year + 1911
    return year


def parse_quarter(value, statement_date: date) -> int:
    if value is not None and value != "":
        text = str(value).strip().upper().replace("Q", "")
        quarter = int(text)
    else:
        quarter = quarter_from_month(statement_date.month)

    if quarter not in {1, 2, 3, 4}:
        raise FinMindMappingError(f"Invalid fiscal quarter: {value}")
    return quarter


def quarter_from_month(month: int) -> int:
    if month in {1, 2, 3}:
        return 1
    if month in {4, 5, 6}:
        return 2
    if month in {7, 8, 9}:
        return 3
    if month in {10, 11, 12}:
        return 4
    raise FinMindMappingError(f"Invalid statement month: {month}")


def parse_date(value) -> date:
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if "/" in text:
        parts = text.split("/")
        if len(parts) == 3:
            year = parse_year(parts[0])
            return date(year, int(parts[1]), int(parts[2]))

    parts = text.split("-")
    if len(parts) == 3:
        year = parse_year(parts[0])
        return date(year, int(parts[1]), int(parts[2]))

    raise FinMindMappingError(f"Invalid FinMind date: {value}")


def parse_optional_float(value) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def build_payload_json(row: dict) -> str:
    excluded_fields = {
        "symbol",
        "stock_id",
        "fiscal_year",
        "year",
        "fiscal_quarter",
        "quarter",
        "statement_date",
        "date",
        "published_date",
        "release_date",
        "filing_date",
        "snapshot_date",
        "statement_type",
        "type",
        "created_at",
        "warning",
    }
    payload = {key: value for key, value in row.items() if key not in excluded_fields}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
