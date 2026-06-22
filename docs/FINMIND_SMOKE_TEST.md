# FinMind Smoke Test Guide

This guide describes a safe manual smoke test for the real FinMind API.

The smoke test must use a test database. Do not write directly to the production historical repository database:

```text
historical_snapshots.db
```

Use this test database instead:

```text
historical_snapshots_test.db
```

## Set FINMIND_TOKEN

PowerShell:

```powershell
$env:FINMIND_TOKEN = "your-finmind-token"
```

The token can also be passed directly:

```powershell
.venv\Scripts\python.exe finmind_import.py --symbol 2330 --start 2024-01-01 --end 2024-12-31 --db historical_snapshots_test.db --token your-finmind-token
```

Token may be empty, but anonymous FinMind access can be rate-limited or unavailable depending on the dataset and FinMind API policy.

## Recommended Smoke Test

Recommended stock:

```text
2330
```

Recommended date range:

```text
2024-01-01 to 2024-12-31
```

Run with the test database:

```powershell
.venv\Scripts\python.exe finmind_import.py --symbol 2330 --start 2024-01-01 --end 2024-12-31 --db historical_snapshots_test.db
```

Or run the helper script:

```powershell
.\scripts\finmind_smoke_test.ps1
```

## Review Summary Report

After the smoke test, open:

```text
reports/finmind_import_summary.md
```

Check:

- `Symbol` is `2330`.
- `Start Date` is `2024-01-01`.
- `End Date` is `2024-12-31`.
- `Repository Database` is `historical_snapshots_test.db`.
- `Imported Count` is greater than zero when FinMind returns data.
- `Failed Count`, `Errors`, and `Warnings` are acceptable for the response being tested.

## Missing Published Date Fallback

FinMind financial statement responses may not include a published date field such as:

- `published_date`
- `release_date`
- `filing_date`

When those fields are missing, StockAnalyzerPro falls back to the statement `date` / `statement_date` so the row can still be imported for research.

Fallback rows are marked with:

```text
warning=missing_published_date
is_point_in_time=false
```

These rows are not formal point-in-time records and should not be treated as look-ahead-safe historical data.

## Latest Smoke Test Result

Real FinMind smoke test result:

| Field | Value |
| --- | --- |
| Symbol | `2330` |
| Start Date | `2024-01-01` |
| End Date | `2024-12-31` |
| Imported Count | `68` |
| Failed Count | `0` |
| Warning Count | `132` |
| SQLite Row Count | `68` |
| Main Warning | `missing_published_date` |
| Point-in-Time Status | `is_point_in_time=false` |

Interpretation:

- FinMind financial statement data can currently be imported successfully into `HistoricalSnapshotRepository`.
- The tested FinMind financial statement response did not provide a formal announcement date field.
- StockAnalyzerPro therefore falls back to `statement_date` / `date` and marks imported rows as `is_point_in_time=false`.
- These imported rows are usable for research and pipeline validation, but they are not formal point-in-time records and should not be treated as look-ahead-safe backtest data.

## Confirm Test Database Has Data

Use Python with SQLite:

```powershell
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('historical_snapshots_test.db'); print(c.execute('select count(*) from financial_statement_snapshots').fetchone()[0]); c.close()"
```

The command prints the number of rows in `financial_statement_snapshots`.

You can also inspect symbols:

```powershell
.venv\Scripts\python.exe -c "import sqlite3; c=sqlite3.connect('historical_snapshots_test.db'); print(c.execute('select distinct symbol from financial_statement_snapshots order by symbol').fetchall()); c.close()"
```

## Delete Test Database

Remove only the test database:

```powershell
Remove-Item .\historical_snapshots_test.db
```

Do not remove or overwrite:

```text
historical_snapshots.db
```

## Safety Checklist

- Use `historical_snapshots_test.db`.
- Confirm `reports/finmind_import_summary.md` points to the test database.
- Do not run the smoke test against `historical_snapshots.db`.
- Do not commit `historical_snapshots_test.db`.
- Delete `historical_snapshots_test.db` after testing.
