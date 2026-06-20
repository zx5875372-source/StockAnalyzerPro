# StockAnalyzerPro

[![Python Tests](https://github.com/zx5875372-source/StockAnalyzerPro/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/zx5875372-source/StockAnalyzerPro/actions/workflows/python-tests.yml)

StockAnalyzerPro is a Python CLI stock analysis project for personal investment research. It focuses on producing a repeatable Markdown report from a fixed investment logic, rather than only fetching market data.

Current version: v1.4 CLI UX Improvement

## Current Features

- Fetches stock and financial data with yfinance.
- Normalizes raw data into FinancialData and FinancialPeriod models.
- Generates a fixed-format Markdown stock analysis report.
- Calculates complete Piotroski F-Score 9 items.
- Calculates SAP Score with a 100-point weighted scoring engine.
- Includes profitability, financial health, cashflow, valuation, and growth analysis.
- Estimates simplified valuation, buy zones, and first target price.
- Shows diagnostics when required financial fields are missing.
- Provides a validation scan over a sample stock universe and exports CSV results.
- Provides an interactive CLI menu for single-stock analysis, watchlist scan, and sample scan.
- Provides a Backtest Engine MVP for historical price validation of SAP Score selections.
- Provides an initial data provider framework for Yahoo Finance, CSV snapshots, and unit-test mocks.

## Installation

Create and activate the Python virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run

Start the CLI:

```powershell
python app.py
```

Or run directly with the project virtual environment:

```powershell
.venv\Scripts\python.exe app.py
```

Main menu:

- `[1]` Analyze a single stock, for example `2330`.
- `[2]` Scan `data/watchlist.json`.
- `[3]` Scan `tests/sample_data/sample_stocks.json`.
- `[4]` Exit.

Reports are generated in the `reports/` folder.

## Batch Scan

You can run scans from the `app.py` menu, or run `scan.py` directly.

Run the default watchlist scan:

```powershell
.venv\Scripts\python.exe scan.py
```

Run the sample universe scan:

```powershell
.venv\Scripts\python.exe scan.py --sample
```

Run the watchlist scan explicitly:

```powershell
.venv\Scripts\python.exe scan.py --watchlist
```

The sample scan reads:

```text
tests/sample_data/sample_stocks.json
```

The watchlist scan reads:

```text
data/watchlist.json
```

The CSV output is written to:

```text
reports/scan_results.csv
```

The scan result includes SAP Score, Piotroski F-Score, fair price, first target price, diagnostics count, runtime, and per-symbol error messages when analysis fails.

v1.2 scan output also includes:

- `missing_count`: number of missing normalized financial fields.
- `missing_fields`: the missing field names.
- `data_quality_score`: `100 - missing_count * 5`, with a minimum of 0.
- `piotroski_available`: number of Piotroski items that can be calculated.
- `valuation_available`: number of valuation base prices available.
- `growth_available`: number of growth rates available.

The CSV is sorted by SAP Score from high to low, then data quality score from high to low.

The scan also writes a summary report:

```text
reports/scan_summary.md
```

Additional ranking reports:

```text
reports/top10.md
reports/watchlist_report.md
```

Use the summary to review total sample count, success rate, average SAP Score, average data quality score, the stocks with the most missing data, and the top 10 SAP Score stocks. Use the watchlist report to review SAP Score, grade, whether price is below the reasonable buy point, first target price, and data quality for your selected stocks.

## Data Layer

Milestone 3 Sprint 1 adds the initial Provider Framework under:

```text
data_provider/
```

The framework introduces:

- `IDataProvider`: stable provider contract for normalized financial data, price history, universes, and diagnostics.
- `YahooFinanceProvider`: yfinance adapter with access to `info`, `financials`, `balance_sheet`, `cashflow`, and `history`.
- `CSVProvider`: strict CSV reader for SAP Score snapshot CSV files.
- `MockProvider`: deterministic in-memory provider for unit tests.
- `ProviderFactory`: factory for `yahoo`, `yfinance`, `yahoo_finance`, `csv`, and `mock`.

Current Sprint boundary:

- `modules/downloader.py` now creates `YahooFinanceProvider` through `ProviderFactory`.
- The public downloader API remains `get_stock_data(symbol)`.
- Analyzer is not changed and still receives `FinancialData`.
- App, scan, and analyzer flows continue to call the existing downloader API.
- Provider Framework is covered by unit tests and is ready for later integration.

## Backtest MVP

Run the Sprint 3 Backtest Engine MVP:

```powershell
.venv\Scripts\python.exe backtest.py
.venv\Scripts\python.exe backtest.py --start 2024-01-01 --end 2025-12-31
.venv\Scripts\python.exe backtest.py --benchmark 006208.TW
.venv\Scripts\python.exe backtest.py --capital 500000
```

Build generated SAP Score snapshots:

```powershell
.venv\Scripts\python.exe snapshot_builder.py
```

The MVP uses:

- `tests/sample_data/sample_stocks.json` as the universe.
- Historical SAP Score snapshots from `data/snapshots/generated_sap_scores.csv` when available.
- Falls back to `data/snapshots/sample_sap_scores.csv` when generated snapshots do not exist.
- Default benchmark `0050.TW`.
- yfinance historical price data from `2023-01-01` to `2025-12-31`.
- Monthly rebalance.
- Equal-weight positions.
- Initial cash of `1000000`.

Outputs:

```text
reports/backtest_summary.md
reports/backtest_equity_curve.csv
```

Snapshot CSV columns:

```text
date,symbol,sap_score,piotroski_score,data_quality_score,source,warning
```

Important limitation: Sprint 3 used current SAP Score signals with historical prices, so its result should not be treated as formal backtest performance. Sprint 4 removes current-score fallback during backtest selection. Sprint 5 adds `generated_sap_scores.csv`, but it is still a proxy marked `source=current_analysis_proxy` and `warning=not_point_in_time`. Formal point-in-time snapshot generation is deferred until historical financial statements are available through FinMind, OpenBB, or another reliable provider.

Backtest credibility grades:

- `A`: look-ahead-safe and all snapshots have no warning.
- `B`: look-ahead-safe but some snapshots have warnings.
- `C`: not look-ahead-safe, or any snapshot has `not_point_in_time`.
- `D`: data is insufficient, or selected stock count is too low.

When the grade is `C` or `D`, the report states that the result is only for system testing and must not be used as investment strategy performance evidence.

Benchmark comparison:

- Backtest reports compare strategy return and CAGR against the benchmark.
- Default benchmark is `0050.TW`.
- If benchmark data is unavailable, the report shows `benchmark unavailable` and records diagnostics.
- Benchmark availability does not directly downgrade credibility.

Backtest CLI options:

- `--start`: start date, default `2023-01-01`.
- `--end`: end date, default `2025-12-31`.
- `--capital`: initial capital, default `1000000`.
- `--benchmark`: benchmark symbol, default `0050.TW`.
- `--snapshot`: snapshot CSV path, default `data/snapshots/generated_sap_scores.csv`.
- `--universe`: universe JSON path, default `tests/sample_data/sample_stocks.json`.

## Tests and CI

Run local checks:

```powershell
.venv\Scripts\python.exe -m py_compile app.py scan.py backtest.py snapshot_builder.py
.venv\Scripts\python.exe -m unittest discover -s tests/unit
```

GitHub Actions runs the same compile and unit test checks on push or pull request to `main` and `develop`.

`scan.py` is not executed in CI because it depends on yfinance network availability.

## Notes

- This project is for research and learning, not investment advice.
- Data quality depends on yfinance availability.
- Future versions may add additional data sources and backtesting workflows, but v1.4 keeps the ranking and watchlist workflow accessible from the CLI menu.
