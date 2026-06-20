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

        diagnostics_rows = "\n".join(f"- {item}" for item in diagnostics) if diagnostics else "- 無"
        selected_rows = "\n".join(f"- {symbol}" for symbol in selected) if selected else "- 無"

        content = f"""# Backtest Summary

Version: Sprint 3 Backtest Engine MVP

## Config

| Item | Value |
|---|---:|
| Start Date | {config['start_date']} |
| End Date | {config['end_date']} |
| Initial Cash | {config['initial_cash']} |
| Rebalance | Monthly |
| Universe | {config['universe_path']} |

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

## Selected Symbols

{selected_rows}

## Diagnostics

{diagnostics_rows}

## Notes

This MVP uses the current SAP Score snapshot with historical price data. It is
not yet a look-ahead-safe historical financial statement backtest.
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
