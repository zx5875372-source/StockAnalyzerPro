from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Callable

from provider_dry_run import SUPPORTED_PROVIDERS, parse_args as parse_single_args, run_dry_run


DEFAULT_WATCHLIST_PATH = Path("data/watchlist.json")
DEFAULT_SAMPLE_PATH = Path("tests/sample_data/sample_stocks.json")
DEFAULT_OUTPUT_PATH = Path("reports/provider_multi_dry_run.md")
DEFAULT_CSV_PATH = Path("reports/provider_multi_dry_run.csv")

CSV_COLUMNS = [
    "symbol",
    "normalized_symbol",
    "symbol_type",
    "selected_provider",
    "fallback_used",
    "fallback_reason",
    "mapped_fields_count",
    "derived_fields_count",
    "missing_fields_count",
    "status",
    "error",
]


DryRunFunc = Callable[[argparse.Namespace], dict[str, Any]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe provider dry-run diagnostics for multiple symbols.",
    )
    parser.add_argument("--provider", choices=SUPPORTED_PROVIDERS, default="composite")
    parser.add_argument("--source", choices=["watchlist", "sample"], default="watchlist")
    parser.add_argument("--symbols", nargs="*")
    parser.add_argument("--show-diagnostics", action="store_true")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--mock", action="store_true")
    return parser.parse_args(argv)


def run_multi_dry_run(
    args: argparse.Namespace,
    dry_run_func: DryRunFunc | None = None,
) -> dict[str, Any]:
    symbols = resolve_symbols(args)
    rows = []
    runner = dry_run_func or _run_single_symbol
    for symbol in symbols:
        single_args = argparse.Namespace(
            provider=args.provider,
            symbol=symbol,
            start=None,
            end=None,
            mock=getattr(args, "mock", False),
            show_diagnostics=getattr(args, "show_diagnostics", False),
        )
        result = runner(single_args)
        rows.append(result_to_row(result))

    summary = build_summary(rows)
    output_path = Path(args.output)
    csv_path = Path(args.csv)
    write_markdown(output_path, rows, summary, show_diagnostics=getattr(args, "show_diagnostics", False))
    write_csv(csv_path, rows)
    return {
        "symbols": symbols,
        "rows": rows,
        "summary": summary,
        "output_path": str(output_path),
        "csv_path": str(csv_path),
    }


def resolve_symbols(args: argparse.Namespace) -> list[str]:
    if getattr(args, "symbols", None):
        return [symbol for symbol in args.symbols if symbol]
    source = getattr(args, "source", "watchlist")
    if source == "sample":
        return load_sample_symbols(DEFAULT_SAMPLE_PATH)
    return load_watchlist_symbols(DEFAULT_WATCHLIST_PATH)


def load_watchlist_symbols(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"watchlist source must be a list: {path}")
    return [str(item) for item in data]


def load_sample_symbols(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"sample source must be a list: {path}")
    symbols = []
    for item in data:
        if isinstance(item, dict) and item.get("symbol"):
            symbols.append(str(item["symbol"]))
        elif isinstance(item, str):
            symbols.append(item)
    return symbols


def result_to_row(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": result.get("symbol") or "",
        "normalized_symbol": result.get("normalized_symbol") or "",
        "symbol_type": result.get("symbol_type") or "",
        "selected_provider": result.get("selected_provider") or "",
        "fallback_used": bool(result.get("fallback_used")),
        "fallback_reason": result.get("fallback_reason") or "",
        "mapped_fields_count": int(result.get("mapped_fields_count") or 0),
        "derived_fields_count": int(result.get("derived_fields_count") or 0),
        "missing_fields_count": int(result.get("missing_fields_count") or 0),
        "status": "success" if result.get("success") else "failed",
        "error": result.get("error") or "",
        "diagnostics": list(result.get("diagnostics") or []),
    }


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_count = len(rows)
    success_count = sum(1 for row in rows if row["status"] == "success")
    failed_count = total_count - success_count
    finmind_count = sum(1 for row in rows if row["selected_provider"] == "finmind")
    yahoo_fallback_count = sum(1 for row in rows if row["fallback_used"])
    missing_rows = [row for row in rows if row["missing_fields_count"] > 0]
    failed_rows = [row for row in rows if row["status"] == "failed"]
    zero_missing_count = sum(1 for row in rows if row["status"] == "success" and row["missing_fields_count"] == 0)
    success_rate = _ratio(success_count, total_count)
    zero_missing_rate = _ratio(zero_missing_count, total_count)
    fallback_rate = _ratio(yahoo_fallback_count, total_count)
    recommended = success_rate >= 0.9 and zero_missing_rate >= 0.8 and fallback_rate <= 0.2
    recommendation = (
        "可考慮進入下一階段 FinMind First runtime integration dry run。"
        if recommended
        else "暫不建議切換 runtime default。"
    )
    return {
        "total_count": total_count,
        "success_count": success_count,
        "failed_count": failed_count,
        "finmind_count": finmind_count,
        "yahoo_fallback_count": yahoo_fallback_count,
        "missing_rows": missing_rows,
        "failed_rows": failed_rows,
        "success_rate": success_rate,
        "zero_missing_rate": zero_missing_rate,
        "fallback_rate": fallback_rate,
        "recommended": recommended,
        "recommendation": recommendation,
    }


def write_markdown(path: Path, rows: list[dict[str, Any]], summary: dict[str, Any], show_diagnostics: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Provider Multi Dry Run",
        "",
        "此報告僅供 FinMind First runtime integration 前的安全驗證，不會切換正式資料來源。",
        "",
        "## Summary",
        "",
        f"- 總檔數: {summary['total_count']}",
        f"- 成功數: {summary['success_count']}",
        f"- 失敗數: {summary['failed_count']}",
        f"- FinMind 使用數: {summary['finmind_count']}",
        f"- Yahoo fallback 數: {summary['yahoo_fallback_count']}",
        f"- success rate: {summary['success_rate']:.0%}",
        f"- missing_fields_count = 0 比率: {summary['zero_missing_rate']:.0%}",
        f"- fallback 比率: {summary['fallback_rate']:.0%}",
        f"- 建議: {summary['recommendation']}",
        "",
        "## Missing Fields > 0",
        "",
    ]
    if summary["missing_rows"]:
        lines.extend([f"- {row['normalized_symbol']}: {row['missing_fields_count']}" for row in summary["missing_rows"]])
    else:
        lines.append("- 無")
    lines.extend(["", "## Failed Stocks", ""])
    if summary["failed_rows"]:
        lines.extend([f"- {row['normalized_symbol']}: {row['error']}" for row in summary["failed_rows"]])
    else:
        lines.append("- 無")

    lines.extend(
        [
            "",
            "## Results",
            "",
            "| 股票代號 | normalized_symbol | symbol_type | selected_provider | fallback_used | mapped | derived | missing | status | error |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )
    for row in rows:
        lines.append(
            "| {symbol} | {normalized_symbol} | {symbol_type} | {selected_provider} | {fallback_used} | "
            "{mapped_fields_count} | {derived_fields_count} | {missing_fields_count} | {status} | {error} |".format(
                **{key: _md(row.get(key, "")) for key in row},
            )
        )
    if show_diagnostics:
        lines.extend(["", "## Diagnostics", ""])
        for row in rows:
            lines.append(f"### {row['normalized_symbol']}")
            diagnostics = row.get("diagnostics") or []
            lines.extend([f"- {_md(item)}" for item in diagnostics] if diagnostics else ["- 無"])
            lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in CSV_COLUMNS})


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = run_multi_dry_run(args)
    summary = result["summary"]
    print("Provider Multi Dry Run")
    print(f"output: {result['output_path']}")
    print(f"csv: {result['csv_path']}")
    print(f"total: {summary['total_count']}")
    print(f"success: {summary['success_count']}")
    print(f"failed: {summary['failed_count']}")
    print(f"recommendation: {summary['recommendation']}")
    return 0


def _run_single_symbol(args: argparse.Namespace) -> dict[str, Any]:
    return run_dry_run(parse_single_args(_single_args_to_argv(args)))


def _single_args_to_argv(args: argparse.Namespace) -> list[str]:
    argv = ["--provider", args.provider, "--symbol", args.symbol]
    if getattr(args, "mock", False):
        argv.append("--mock")
    if getattr(args, "show_diagnostics", False):
        argv.append("--show-diagnostics")
    return argv


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _md(value: Any) -> str:
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text if text else "-"


if __name__ == "__main__":
    raise SystemExit(main())
