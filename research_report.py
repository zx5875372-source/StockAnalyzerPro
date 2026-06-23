import argparse
import csv
from pathlib import Path


DEFAULT_INPUT_PATH = Path("reports/strategy_comparison.csv")
DEFAULT_OUTPUT_PATH = Path("reports/research_report.md")
REQUIRED_COLUMNS = {
    "strategy",
    "total_return",
    "cagr",
    "max_drawdown",
    "win_rate",
    "benchmark_total_return",
    "excess_return",
    "credibility_grade",
    "selected_stock_count",
    "skipped_stock_count",
    "strategy_vs_benchmark",
}
CREDIBILITY_MEANING = {
    "A": "可信度高，適合進一步策略審查。",
    "B": "可信度中等，結果可供研究，但仍有已知限制。",
    "C": "屬於 proxy 等級可信度，結果僅供研究。",
    "D": "可信度低，結果僅供系統測試與研究。",
}


class ResearchReportError(ValueError):
    pass


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="產生 StockAnalyzerPro 研究報告")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH), help="策略比較 CSV 路徑")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="研究報告 Markdown 路徑")
    return parser


def read_strategy_comparison(path: Path = DEFAULT_INPUT_PATH) -> list[dict]:
    if not path.exists():
        raise ResearchReportError(f"找不到策略比較 CSV：{path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing_columns:
            raise ResearchReportError(
                "策略比較 CSV 缺少欄位：" + ", ".join(missing_columns)
            )
        rows = [normalize_row(row) for row in reader]

    if not rows:
        raise ResearchReportError(f"策略比較 CSV 是空的：{path}")

    return rows


def normalize_row(row: dict) -> dict:
    normalized = dict(row)
    for field in [
        "total_return",
        "cagr",
        "max_drawdown",
        "win_rate",
        "benchmark_total_return",
        "excess_return",
    ]:
        normalized[field] = parse_optional_float(row.get(field))
    for field in ["selected_stock_count", "skipped_stock_count"]:
        normalized[field] = parse_int(row.get(field))
    normalized["research_only_count"] = parse_int(row.get("research_only_count"))
    normalized["credibility_grade"] = (row.get("credibility_grade") or "").strip().upper()
    normalized["qualification_grade"] = (row.get("qualification_grade") or "N/A").strip().upper()
    normalized["qualification_reason"] = row.get("qualification_reason") or ""
    normalized["is_formal_point_in_time"] = parse_bool(row.get("is_formal_point_in_time"))
    return normalized


def generate_research_report(rows: list[dict]) -> str:
    if not rows:
        raise ResearchReportError("策略比較資料列是空的")

    ranked_rows = rank_by_excess_return(rows)
    best = ranked_rows[0]
    benchmark_beaten = best["strategy_vs_benchmark"] == "outperform"
    low_credibility = any(row["credibility_grade"] in {"C", "D"} for row in rows)
    qualification = qualification_summary(rows)

    return f"""# 研究報告

## 執行摘要

- 最佳策略：{best['strategy']}
- 是否勝過基準：{'是' if benchmark_beaten else '否'}
- 可信度評級：{best['credibility_grade']}
- 最佳超額報酬率：{format_percent(best['excess_return'])}
- 正式 Point-in-Time 策略數：{qualification['formal_count']}
- 僅供研究策略數：{qualification['research_only_count']}
- 僅供研究提醒：{qualification['notice']}

## 策略排名

{strategy_ranking_table(ranked_rows)}

## 風險比較

{risk_comparison_table(rows)}

## 可信度分析

{credibility_analysis(rows)}

## 回測資格分析

{qualification_analysis(rows)}

## 建議

{recommendation(rows, low_credibility, qualification['research_only_count'] > 0)}
"""


def rank_by_excess_return(rows: list[dict]) -> list[dict]:
    return sorted(
        rows,
        key=lambda row: row["excess_return"] if row["excess_return"] is not None else float("-inf"),
        reverse=True,
    )


def strategy_ranking_table(rows: list[dict]) -> str:
    table_rows = "\n".join(
        [
            f"| {index} | {row['strategy']} | {format_percent(row['excess_return'])} | "
            f"{format_percent(row['total_return'])} | {format_percent(row['cagr'])} | "
            f"{row['credibility_grade']} | {format_strategy_vs_benchmark(row['strategy_vs_benchmark'])} |"
            for index, row in enumerate(rows, start=1)
        ]
    )
    return f"""| 排名 | 策略 | 超額報酬率 | 總報酬率 | 年化報酬率 | 可信度 | 是否勝過基準 |
|---:|---|---:|---:|---:|---|---|
{table_rows}"""


def risk_comparison_table(rows: list[dict]) -> str:
    table_rows = "\n".join(
        [
            f"| {row['strategy']} | {format_percent(row['max_drawdown'])} | "
            f"{format_percent(row['win_rate'])} | {row['selected_stock_count']} | "
            f"{row['skipped_stock_count']} |"
            for row in rows
        ]
    )
    return f"""| 策略 | 最大回撤 | 勝率 | 入選 | 略過 |
|---|---:|---:|---:|---:|
{table_rows}"""


def credibility_analysis(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        grade = row["credibility_grade"]
        meaning = CREDIBILITY_MEANING.get(grade, "未知可信度評級。")
        lines.append(f"- {row['strategy']}：評級 {grade}。{meaning}")

    lines.append("")
    lines.append("A/B/C/D 解讀：")
    lines.append("- A：可信度最高，適合正式審查。")
    lines.append("- B：可用的研究結果，但有明確限制。")
    lines.append("- C：存在 proxy 資料或 snapshot warning 風險。")
    lines.append("- D：資料不足或可信度偏低。")
    lines.append("")
    lines.append("Snapshot warning / look-ahead-safe 分析：")
    lines.append(
        "- 本報告僅根據策略比較輸出產生。"
        "若策略評級為 C 或 D，代表可能存在 snapshot warning、"
        "look-ahead 風險、入選樣本不足或其他可信度限制。"
    )
    return "\n".join(lines)


def qualification_summary(rows: list[dict]) -> dict:
    formal_count = sum(1 for row in rows if row.get("is_formal_point_in_time"))
    research_only_count = sum(1 for row in rows if is_research_only_strategy(row))
    if research_only_count > 0:
        notice = "僅供研究策略不可視為正式 Point-in-Time 投資績效。"
    else:
        notice = "本次策略比較未標示僅供研究策略。"
    return {
        "formal_count": formal_count,
        "research_only_count": research_only_count,
        "notice": notice,
    }


def qualification_analysis(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        formal = "是" if row.get("is_formal_point_in_time") else "否"
        research_only = "是" if is_research_only_strategy(row) else "否"
        lines.append(
            f"- {row['strategy']}：回測資格評級 {row.get('qualification_grade', 'N/A')}。"
            f"正式 Point-in-Time：{formal}。僅供研究：{research_only}。"
            f"{row.get('qualification_reason') or '未提供回測資格原因。'}"
        )
    return "\n".join(lines)


def is_research_only_strategy(row: dict) -> bool:
    if row.get("is_formal_point_in_time"):
        return False
    qualification_grade = row.get("qualification_grade", "N/A")
    if qualification_grade == "N/A":
        return False
    return row.get("research_only_count", 0) > 0 or qualification_grade in {"C", "D"}


def recommendation(rows: list[dict], low_credibility: bool, has_research_only: bool = False) -> str:
    best = rank_by_excess_return(rows)[0]
    if low_credibility or has_research_only:
        return (
            f"{best['strategy']} 在本次比較中有最高超額報酬率，"
            "但至少一項結果屬於 C/D 可信度或僅供研究資格。"
            "目前結果僅供研究，不可視為正式投資績效。"
        )
    return (
        f"{best['strategy']} 是本次比較中的優先候選策略。"
        "正式使用於投資決策前，仍需進一步驗證。"
    )


def write_research_report(rows: list[dict], output_path: Path = DEFAULT_OUTPUT_PATH) -> None:
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(generate_research_report(rows), encoding="utf-8")


def parse_optional_float(value):
    if value in {None, "", "benchmark unavailable"}:
        return None
    return float(value)


def parse_int(value) -> int:
    if value in {None, ""}:
        return 0
    return int(float(value))


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes"}


def format_percent(value) -> str:
    if value is None:
        return "基準資料不足"
    return f"{value * 100:.2f}%"


def format_strategy_vs_benchmark(value: str) -> str:
    if value == "outperform":
        return "是"
    if value == "underperform":
        return "否"
    return "基準資料不足"


def main(argv=None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        rows = read_strategy_comparison(Path(args.input))
        write_research_report(rows, Path(args.output))
    except ResearchReportError as error:
        parser.error(str(error))

    print("====================================")
    print(" StockAnalyzerPro 研究報告")
    print("====================================")
    print(f"輸入檔案：{args.input}")
    print(f"輸出報告：{args.output}")


if __name__ == "__main__":
    main()
