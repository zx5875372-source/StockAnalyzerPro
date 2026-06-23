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

        content = f"""# 回測摘要

版本：Sprint 8 Backtest CLI Options

## 回測設定

| 項目 | 數值 |
|---|---:|
| 開始日期 | {config['start_date']} |
| 結束日期 | {config['end_date']} |
| 初始資金 | {config['initial_cash']} |
| 再平衡 | 每月 |
| 基準指數 | {config['benchmark_symbol']} |
| 策略 | {result['strategy_name']} |
| 股票範圍 | {config['universe_path']} |
| 快照來源 | {result['snapshot_source']} |
| 無未來函數 | {str(result['look_ahead_safe']).lower()} |
| 快照 Point-in-Time | {str(result['snapshot_point_in_time']).lower()} |

## 可信度

| 項目 | 數值 |
|---|---|
| 可信度評級 | {result['credibility_grade']} |
| 可信度原因 | {result['credibility_reason']} |

{credibility_notice}

## 回測資格

| 項目 | 數值 |
|---|---:|
| 回測資格評級 | {result['qualification_grade']} |
| 回測資格原因 | {result['qualification_reason']} |
| 僅供研究筆數 | {result['research_only_count']} |
| Point-in-Time 筆數 | {result['point_in_time_count']} |
| 缺少公告日筆數 | {result['missing_published_date_count']} |
| 非 Point-in-Time 筆數 | {result['not_point_in_time_count']} |

{qualification_notice}

## 策略條件

| 項目 | 數值 |
|---|---:|
| 策略 | {result['strategy_name']} |
| SAP Score >= | {config['min_sap_score']} |
| Piotroski >= | {config['min_piotroski_score']} |
| 資料品質 >= | {config['min_data_quality_score']} |

## 績效表現

| 指標 | 數值 |
|---|---:|
| 總報酬率 | {format_percent(metrics['total_return'])} |
| 年化報酬率 | {format_percent(metrics['cagr'])} |
| 最大回撤 | {format_percent(metrics['max_drawdown'])} |
| 勝率 | {format_percent(metrics['win_rate'])} |
| Sharpe | TODO |
| Sortino | TODO |

## 基準比較

| 指標 | 數值 |
|---|---:|
| 策略總報酬率 | {format_percent(metrics['total_return'])} |
| 策略年化報酬率 | {format_percent(metrics['cagr'])} |
| 基準指數 | {config['benchmark_symbol']} |
| 基準總報酬率 | {format_percent(metrics['benchmark_total_return'])} |
| 基準年化報酬率 | {format_percent(metrics['benchmark_cagr'])} |
| 超額報酬率 | {format_percent(metrics['excess_return'])} |
| 超額年化報酬率 | {format_percent(metrics['excess_cagr'])} |
| 是否勝過基準 | {format_benchmark_result(metrics['strategy_vs_benchmark'])} |

## 資料完整性

| 項目 | 數值 |
|---|---:|
| 快照來源 | {result['snapshot_source']} |
| 無未來函數 | {str(result['look_ahead_safe']).lower()} |
| 快照 Point-in-Time | {str(result['snapshot_point_in_time']).lower()} |
| 回測資格評級 | {result['qualification_grade']} |
| 僅供研究筆數 | {result['research_only_count']} |
| Point-in-Time 筆數 | {result['point_in_time_count']} |
| 缺少公告日筆數 | {result['missing_published_date_count']} |
| 非 Point-in-Time 筆數 | {result['not_point_in_time_count']} |
| 入選股票數 | {result['selected_stock_count']} |
| 略過股票數 | {result['skipped_stock_count']} |

## 快照警告

| 警告 | 筆數 |
|---|---:|
{warning_rows}

## 入選股票

{selected_rows}

## 略過原因

{skipped_rows}

## 診斷訊息

{diagnostics_rows}

## 備註

此回測使用設定來源中的歷史 SAP Score 快照。
回測選股期間不會 fallback 到目前分數。標示為 `current_analysis_proxy`
與 `not_point_in_time` 的快照屬於 proxy 資料，
不可視為正式 point-in-time 財報快照。
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
        return "基準資料不足"
    return f"{value * 100:.2f}%"


def format_benchmark_result(value: str) -> str:
    if value == "outperform":
        return "是"
    if value == "underperform":
        return "否"
    return "基準資料不足"
