Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$DbPath = "historical_pipeline_test.db"
$FinancialCsv = "tests/sample_data/historical/financial_snapshots_valid.csv"
$ReportPath = "reports/historical_pipeline_smoke_test.md"

if (Test-Path -LiteralPath $DbPath) {
    Remove-Item -LiteralPath $DbPath
}

.venv\Scripts\python.exe historical_import.py --type financial --file $FinancialCsv --db $DbPath
.venv\Scripts\python.exe historical_generate_sap.py --db $DbPath

@"
import re
import sqlite3
from pathlib import Path

db_path = Path("$DbPath")
report_path = Path("$ReportPath")
generator_summary_path = Path("reports/historical_generator_summary.md")

with sqlite3.connect(db_path) as connection:
    financial_count = connection.execute(
        "SELECT COUNT(*) FROM financial_statement_snapshots"
    ).fetchone()[0]
    sap_count = connection.execute(
        "SELECT COUNT(*) FROM sap_score_snapshots"
    ).fetchone()[0]
    warning_rows = connection.execute(
        "SELECT warning FROM sap_score_snapshots WHERE warning IS NOT NULL AND warning != ''"
    ).fetchall()
    point_in_time_rows = connection.execute(
        "SELECT is_point_in_time, COUNT(*) FROM sap_score_snapshots GROUP BY is_point_in_time ORDER BY is_point_in_time"
    ).fetchall()

generator_summary = generator_summary_path.read_text(encoding="utf-8") if generator_summary_path.exists() else ""
failed_match = re.search(r"\| Failed \| ([0-9]+) \|", generator_summary)
failed_count = int(failed_match.group(1)) if failed_match else 0

warnings = [row[0] for row in warning_rows]
point_in_time_status = ", ".join(
    f"{'true' if status else 'false'}={count}" for status, count in point_in_time_rows
) or "none"

lines = [
    "# Historical Pipeline Smoke Test",
    "",
    "| Field | Value |",
    "| --- | --- |",
    f"| Database | {db_path} |",
    f"| Imported Financial Snapshots | {financial_count} |",
    f"| Generated SAP Snapshots | {sap_count} |",
    f"| Failed Count | {failed_count} |",
    f"| Warning Count | {len(warnings)} |",
    f"| Point-in-Time Status | {point_in_time_status} |",
    "",
    "## Warnings",
    "",
]

if warnings:
    lines.extend(f"- {warning}" for warning in warnings)
else:
    lines.append("- None")

report_path.parent.mkdir(parents=True, exist_ok=True)
report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"historical_pipeline_smoke_test_report={report_path}")
"@ | .venv\Scripts\python.exe -
