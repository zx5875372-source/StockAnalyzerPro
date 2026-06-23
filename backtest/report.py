import csv
from datetime import datetime, timezone
import json
from pathlib import Path


SUMMARY_PATH = Path("reports/backtest_summary.md")
EQUITY_CURVE_PATH = Path("reports/backtest_equity_curve.csv")
QUALIFICATION_CSV_PATH = Path("reports/backtest_qualification.csv")
QUALIFICATION_JSON_PATH = Path("reports/backtest_qualification.json")


class BacktestReportWriter:
    def __init__(
        self,
        summary_path: Path = SUMMARY_PATH,
        equity_curve_path: Path = EQUITY_CURVE_PATH,
        qualification_csv_path: Path = QUALIFICATION_CSV_PATH,
        qualification_json_path: Path = QUALIFICATION_JSON_PATH,
    ):
        self.summary_path = summary_path
        self.equity_curve_path = equity_curve_path
        self.qualification_csv_path = qualification_csv_path
        self.qualification_json_path = qualification_json_path

    def write(self, result: dict) -> None:
        self.write_markdown(result)
        self.write_equity_curve_csv(result)
        self.write_qualification_csv(result)
        self.write_qualification_json(result)

    def write_markdown(self, result: dict) -> None:
        self.summary_path.parent.mkdir(exist_ok=True)
        metrics = result["metrics"]
        config = result["config"]
        diagnostics = result.get("diagnostics", [])
        selected = result.get("selected_symbols", [])
        skipped_reasons = result.get("skipped_reasons", {})
        warning_counts = result.get("snapshot_warning_counts", {})
        credibility_notice = result.get("credibility_notice", "")
        qualification_notice = result.get("qualification_notice", "")

        diagnostics_rows = "\n".join(f"- {item}" for item in diagnostics) if diagnostics else "- 無"
        selected_rows = "\n".join(f"- {symbol}" for symbol in selected) if selected else "- 無"
        skipped_rows = (
            "\n".join(f"- {symbol}: {reason}" for symbol, reason in sorted(skipped_reasons.items()))
            if skipped_reasons
            else "- 無"
        )
        warning_rows = (
            "\n".join(f"| {warning} | {count} |" for warning, count in sorted(warning_counts.items()))
            if warning_counts
            else "| 無 | 0 |"
        )

        content = f"""# Backtest Summary

Version: Sprint 8 Backtest CLI Options

## Config

| Item | Value |
|---|---:|
| Start Date | {config['start_date']} |
| End Date | {config['end_date']} |
| Initial Cash | {config['initial_cash']} |
| Rebalance | Monthly |
| Benchmark | {config['benchmark_symbol']} |
| Strategy | {result['strategy_name']} |
| Universe | {config['universe_path']} |
| Snapshot Source | {result['snapshot_source']} |
| Look-ahead-safe | {str(result['look_ahead_safe']).lower()} |
| Snapshot Point-in-time | {str(result['snapshot_point_in_time']).lower()} |

## Credibility

| Item | Value |
|---|---|
| Credibility Grade | {result['credibility_grade']} |
| Credibility Reason | {result['credibility_reason']} |

{credibility_notice}

## Historical Qualification

| Item | Value |
|---|---:|
| Qualification Grade | {result['qualification_grade']} |
| Qualification Reason | {result['qualification_reason']} |
| Research-only Count | {result['research_only_count']} |
| Point-in-Time Count | {result['point_in_time_count']} |
| Missing Published Date Count | {result['missing_published_date_count']} |
| Not Point-in-Time Count | {result['not_point_in_time_count']} |

{qualification_notice}

## Strategy

| Item | Value |
|---|---:|
| Strategy | {result['strategy_name']} |
| SAP Score >= | {config['min_sap_score']} |
| Piotroski >= | {config['min_piotroski_score']} |
| Data Quality >= | {config['min_data_quality_score']} |

## Performance

| Metric | Value |
|---|---:|
| Total Return | {format_percent(metrics['total_return'])} |
| CAGR | {format_percent(metrics['cagr'])} |
| Max Drawdown | {format_percent(metrics['max_drawdown'])} |
| Win Rate | {format_percent(metrics['win_rate'])} |
| Sharpe | TODO |
| Sortino | TODO |

## Benchmark Comparison

| Metric | Value |
|---|---:|
| Strategy Total Return | {format_percent(metrics['total_return'])} |
| Strategy CAGR | {format_percent(metrics['cagr'])} |
| Benchmark | {config['benchmark_symbol']} |
| Benchmark Total Return | {format_percent(metrics['benchmark_total_return'])} |
| Benchmark CAGR | {format_percent(metrics['benchmark_cagr'])} |
| Excess Return | {format_percent(metrics['excess_return'])} |
| Excess CAGR | {format_percent(metrics['excess_cagr'])} |
| Strategy vs Benchmark | {format_benchmark_result(metrics['strategy_vs_benchmark'])} |

## Data Integrity

| Item | Value |
|---|---:|
| Snapshot Source | {result['snapshot_source']} |
| Look-ahead-safe | {str(result['look_ahead_safe']).lower()} |
| Snapshot Point-in-time | {str(result['snapshot_point_in_time']).lower()} |
| Qualification Grade | {result['qualification_grade']} |
| Research-only Count | {result['research_only_count']} |
| Point-in-Time Count | {result['point_in_time_count']} |
| Missing Published Date Count | {result['missing_published_date_count']} |
| Not Point-in-Time Count | {result['not_point_in_time_count']} |
| Selected Stock Count | {result['selected_stock_count']} |
| Skipped Stock Count | {result['skipped_stock_count']} |

## Snapshot Warnings

| Warning | Count |
|---|---:|
{warning_rows}

## Selected Symbols

{selected_rows}

## Skipped Reasons

{skipped_rows}

## Diagnostics

{diagnostics_rows}

## Notes

This MVP uses historical SAP Score snapshots from the configured snapshot source.
It does not fallback to current scores during backtest selection. Generated
snapshots marked `current_analysis_proxy` and `not_point_in_time` are proxy data,
not formal point-in-time financial statement snapshots.
"""
        self.summary_path.write_text(content, encoding="utf-8")

    def write_equity_curve_csv(self, result: dict) -> None:
        self.equity_curve_path.parent.mkdir(exist_ok=True)
        with self.equity_curve_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(
                file,
                fieldnames=["date", "total_value", "cash", "positions"],
            )
            writer.writeheader()
            writer.writerows(result["equity_curve"])

    def write_qualification_csv(self, result: dict) -> None:
        self.qualification_csv_path.parent.mkdir(exist_ok=True)
        row = build_qualification_export_row(result)
        with self.qualification_csv_path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=list(row.keys()))
            writer.writeheader()
            writer.writerow(row)

    def write_qualification_json(self, result: dict) -> None:
        self.qualification_json_path.parent.mkdir(exist_ok=True)
        row = build_qualification_export_row(result)
        self.qualification_json_path.write_text(
            json.dumps(row, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def build_qualification_export_row(result: dict) -> dict:
    config = result.get("config", {})
    return {
        "snapshot_source": config.get("snapshot_source", "csv"),
        "snapshot_db": config.get("snapshot_db_path", ""),
        "qualification_grade": result.get("qualification_grade", "N/A"),
        "qualification_reason": result.get("qualification_reason", ""),
        "research_only_count": result.get("research_only_count", 0),
        "point_in_time_count": result.get("point_in_time_count", 0),
        "missing_published_date_count": result.get("missing_published_date_count", 0),
        "not_point_in_time_count": result.get("not_point_in_time_count", 0),
        "is_formal_point_in_time": bool(result.get("is_formal_point_in_time", False)),
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def format_percent(value) -> str:
    if value is None:
        return "benchmark unavailable"
    return f"{value * 100:.2f}%"


def format_benchmark_result(value: str) -> str:
    if value == "outperform":
        return "是"
    if value == "underperform":
        return "否"
    return "benchmark unavailable"
