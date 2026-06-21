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
    "A": "High credibility. Results are suitable for deeper strategy review.",
    "B": "Moderate credibility. Results are useful, with known limitations.",
    "C": "Proxy-level credibility. Results are for research only.",
    "D": "Low credibility. Results are for system testing and research only.",
}


class ResearchReportError(ValueError):
    pass


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate StockAnalyzerPro research report")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH), help="strategy comparison CSV path")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="research report Markdown path")
    return parser


def read_strategy_comparison(path: Path = DEFAULT_INPUT_PATH) -> list[dict]:
    if not path.exists():
        raise ResearchReportError(f"strategy comparison CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        fieldnames = set(reader.fieldnames or [])
        missing_columns = sorted(REQUIRED_COLUMNS - fieldnames)
        if missing_columns:
            raise ResearchReportError(
                "strategy comparison CSV missing columns: " + ", ".join(missing_columns)
            )
        rows = [normalize_row(row) for row in reader]

    if not rows:
        raise ResearchReportError(f"strategy comparison CSV is empty: {path}")

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
    normalized["credibility_grade"] = (row.get("credibility_grade") or "").strip().upper()
    return normalized


def generate_research_report(rows: list[dict]) -> str:
    if not rows:
        raise ResearchReportError("strategy comparison rows are empty")

    ranked_rows = rank_by_excess_return(rows)
    best = ranked_rows[0]
    benchmark_beaten = best["strategy_vs_benchmark"] == "outperform"
    low_credibility = any(row["credibility_grade"] in {"C", "D"} for row in rows)

    return f"""# Research Report

## Executive Summary

- Best Strategy: {best['strategy']}
- Benchmark Beaten: {'Yes' if benchmark_beaten else 'No'}
- Credibility Rating: {best['credibility_grade']}
- Best Excess Return: {format_percent(best['excess_return'])}

## Strategy Ranking

{strategy_ranking_table(ranked_rows)}

## Risk Comparison

{risk_comparison_table(rows)}

## Credibility Analysis

{credibility_analysis(rows)}

## Recommendation

{recommendation(rows, low_credibility)}
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
            f"{row['credibility_grade']} | {row['strategy_vs_benchmark']} |"
            for index, row in enumerate(rows, start=1)
        ]
    )
    return f"""| Rank | Strategy | Excess Return | Total Return | CAGR | Credibility | Strategy vs Benchmark |
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
    return f"""| Strategy | Max Drawdown | Win Rate | Selected | Skipped |
|---|---:|---:|---:|---:|
{table_rows}"""


def credibility_analysis(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        grade = row["credibility_grade"]
        meaning = CREDIBILITY_MEANING.get(grade, "Unknown credibility grade.")
        lines.append(f"- {row['strategy']}: Grade {grade}. {meaning}")

    lines.append("")
    lines.append("A/B/C/D interpretation:")
    lines.append("- A: highest confidence, suitable for formal review.")
    lines.append("- B: usable research result with visible limitations.")
    lines.append("- C: proxy data or snapshot warning risk is present.")
    lines.append("- D: insufficient or low-confidence result.")
    lines.append("")
    lines.append("Snapshot warning / look-ahead-safe analysis:")
    lines.append(
        "- This report is generated from strategy comparison output only. "
        "If a strategy is graded C or D, treat that as evidence of snapshot warnings, "
        "look-ahead risk, insufficient selection count, or other credibility limits."
    )
    return "\n".join(lines)


def recommendation(rows: list[dict], low_credibility: bool) -> str:
    best = rank_by_excess_return(rows)[0]
    if low_credibility:
        return (
            f"{best['strategy']} has the highest excess return in this comparison, "
            "but at least one result has C/D credibility. "
            "目前結果僅供研究，不可視為正式投資績效。"
        )
    return (
        f"{best['strategy']} is the preferred candidate from this comparison. "
        "Proceed with deeper validation before using it in production decisions."
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


def format_percent(value) -> str:
    if value is None:
        return "benchmark unavailable"
    return f"{value * 100:.2f}%"


def main(argv=None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        rows = read_strategy_comparison(Path(args.input))
        write_research_report(rows, Path(args.output))
    except ResearchReportError as error:
        parser.error(str(error))

    print("====================================")
    print(" StockAnalyzerPro Research Report")
    print("====================================")
    print(f"Input：{args.input}")
    print(f"Output：{args.output}")


if __name__ == "__main__":
    main()
