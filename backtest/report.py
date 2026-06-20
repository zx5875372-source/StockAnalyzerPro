import csv
from pathlib import Path


SUMMARY_PATH = Path("reports/backtest_summary.md")
EQUITY_CURVE_PATH = Path("reports/backtest_equity_curve.csv")


class BacktestReportWriter:
    def __init__(
        self,
        summary_path: Path = SUMMARY_PATH,
        equity_curve_path: Path = EQUITY_CURVE_PATH,
    ):
        self.summary_path = summary_path
        self.equity_curve_path = equity_curve_path

    def write(self, result: dict) -> None:
        self.write_markdown(result)
        self.write_equity_curve_csv(result)

    def write_markdown(self, result: dict) -> None:
        self.summary_path.parent.mkdir(exist_ok=True)
        metrics = result["metrics"]
        config = result["config"]
        diagnostics = result.get("diagnostics", [])
        selected = result.get("selected_symbols", [])
        skipped_reasons = result.get("skipped_reasons", {})

        diagnostics_rows = "\n".join(f"- {item}" for item in diagnostics) if diagnostics else "- 無"
        selected_rows = "\n".join(f"- {symbol}" for symbol in selected) if selected else "- 無"
        skipped_rows = (
            "\n".join(f"- {symbol}: {reason}" for symbol, reason in sorted(skipped_reasons.items()))
            if skipped_reasons
            else "- 無"
        )

        content = f"""# Backtest Summary

Version: Sprint 4 Backtest Data Integrity

## Config

| Item | Value |
|---|---:|
| Start Date | {config['start_date']} |
| End Date | {config['end_date']} |
| Initial Cash | {config['initial_cash']} |
| Rebalance | Monthly |
| Universe | {config['universe_path']} |
| Snapshot Source | {result['snapshot_source']} |
| Look-ahead-safe | {str(result['look_ahead_safe']).lower()} |

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

## Data Integrity

| Item | Value |
|---|---:|
| Snapshot Source | {result['snapshot_source']} |
| Look-ahead-safe | {str(result['look_ahead_safe']).lower()} |
| Selected Stock Count | {result['selected_stock_count']} |
| Skipped Stock Count | {result['skipped_stock_count']} |

## Selected Symbols

{selected_rows}

## Skipped Reasons

{skipped_rows}

## Diagnostics

{diagnostics_rows}

## Notes

This MVP uses historical SAP Score snapshots from the configured snapshot source.
It does not fallback to current scores. The sample snapshot file is still a
simplified fixture and not a complete point-in-time financial statement dataset.
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


def format_percent(value) -> str:
    if value is None:
        return "TODO"
    return f"{value * 100:.2f}%"
