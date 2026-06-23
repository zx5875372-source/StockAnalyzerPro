from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
from pathlib import Path


DEFAULT_REPORT_PATH = Path("reports/v2_4_rc_validation.md")
DEFAULT_QUALIFICATION_JSON_PATH = Path("reports/backtest_qualification.json")


@dataclass
class RCValidationSummary:
    import_status: str
    generator_status: str
    backtest_status: str
    strategy_comparison_status: str
    research_report_status: str
    qualification: dict = field(default_factory=dict)
    known_limitations: list[str] = field(default_factory=list)


DEFAULT_KNOWN_LIMITATIONS = [
    "FinMind financial statement rows without published_date use statement_date/date fallback.",
    "Fallback rows are marked is_point_in_time=false and are research-only.",
    "RC validation uses sample historical fixtures and may still depend on yfinance price availability during backtest.",
    "This validation does not create a GitHub Release or push commits.",
]


def load_qualification_summary(path: str | Path = DEFAULT_QUALIFICATION_JSON_PATH) -> dict:
    qualification_path = Path(path)
    if not qualification_path.exists():
        return {
            "snapshot_source": "unknown",
            "snapshot_db": "",
            "qualification_grade": "unknown",
            "qualification_reason": f"qualification export not found: {qualification_path}",
            "research_only_count": 0,
            "point_in_time_count": 0,
            "missing_published_date_count": 0,
            "not_point_in_time_count": 0,
            "is_formal_point_in_time": False,
            "generated_at": "",
        }
    with qualification_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_validation_report(summary: RCValidationSummary) -> str:
    qualification = summary.qualification
    formal_status = "formal" if qualification.get("is_formal_point_in_time") else "research-only"
    limitations = summary.known_limitations or DEFAULT_KNOWN_LIMITATIONS
    lines = [
        "# v2.4 Historical Backtesting RC Validation",
        "",
        "| Step | Status |",
        "| --- | --- |",
        f"| Import | {summary.import_status} |",
        f"| Generator | {summary.generator_status} |",
        f"| Backtest | {summary.backtest_status} |",
        f"| Strategy Comparison | {summary.strategy_comparison_status} |",
        f"| Research Report | {summary.research_report_status} |",
        "",
        "## Qualification Summary",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Snapshot Source | {qualification.get('snapshot_source', 'unknown')} |",
        f"| Snapshot DB | {qualification.get('snapshot_db', '')} |",
        f"| Qualification Grade | {qualification.get('qualification_grade', 'unknown')} |",
        f"| Qualification Reason | {qualification.get('qualification_reason', '')} |",
        f"| Research-only Count | {qualification.get('research_only_count', 0)} |",
        f"| Point-in-Time Count | {qualification.get('point_in_time_count', 0)} |",
        f"| Missing Published Date Count | {qualification.get('missing_published_date_count', 0)} |",
        f"| Not Point-in-Time Count | {qualification.get('not_point_in_time_count', 0)} |",
        f"| Is Formal Point-in-Time | {str(qualification.get('is_formal_point_in_time', False)).lower()} |",
        f"| Generated At | {qualification.get('generated_at', '')} |",
        "",
        "## Formal PIT / Research-only Status",
        "",
        f"- RC validation status: {formal_status}",
    ]
    if not qualification.get("is_formal_point_in_time"):
        lines.append("- 此回測僅供研究與系統驗證，不可視為正式 point-in-time 投資績效。")

    lines.extend(["", "## Known Limitations", ""])
    lines.extend(f"- {limitation}" for limitation in limitations)
    return "\n".join(lines) + "\n"


def write_validation_report(
    summary: RCValidationSummary,
    output_path: str | Path = DEFAULT_REPORT_PATH,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(build_validation_report(summary), encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write v2.4 RC validation summary report")
    parser.add_argument("--import-status", required=True)
    parser.add_argument("--generator-status", required=True)
    parser.add_argument("--backtest-status", required=True)
    parser.add_argument("--strategy-comparison-status", required=True)
    parser.add_argument("--research-report-status", required=True)
    parser.add_argument("--qualification-json", default=str(DEFAULT_QUALIFICATION_JSON_PATH))
    parser.add_argument("--output", default=str(DEFAULT_REPORT_PATH))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    summary = RCValidationSummary(
        import_status=args.import_status,
        generator_status=args.generator_status,
        backtest_status=args.backtest_status,
        strategy_comparison_status=args.strategy_comparison_status,
        research_report_status=args.research_report_status,
        qualification=load_qualification_summary(args.qualification_json),
        known_limitations=DEFAULT_KNOWN_LIMITATIONS,
    )
    write_validation_report(summary, args.output)
    print(f"v2_4_rc_validation_report={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
