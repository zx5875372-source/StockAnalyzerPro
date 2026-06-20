# Changelog

## Sprint 3 - Backtest Engine MVP

- Added Backtest Engine MVP modules under `backtest/`.
- Added `BaseStrategy` and `SAPScoreStrategy`.
- Added MVP portfolio, performance, and report layers.
- Added executable `backtest.py`.
- Outputs `reports/backtest_summary.md` and `reports/backtest_equity_curve.csv`.
- Added unit tests for strategy, portfolio, performance, and engine MVP behavior.
- Documented the MVP limitation: current SAP Score snapshot with historical prices, not yet full historical financial statement scoring.

## CI - GitHub Actions 自動測試

- Added `.github/workflows/python-tests.yml`.
- Runs on push and pull request to `main` and `develop`.
- Installs Python dependencies from `requirements.txt`.
- Compiles `app.py` and `scan.py`.
- Runs unit tests under `tests/unit`.
- Keeps `scan.py` out of CI to avoid network-dependent yfinance failures.

## v1.4 - CLI UX Improvement

- Added an interactive main menu in `app.py`.
- Kept single-stock analysis under menu option 1.
- Added menu options for watchlist scan and sample stock scan.
- Extracted reusable `run_scan(mode="watchlist")` in `scan.py`.
- Preserved existing `scan.py`, `scan.py --sample`, and `scan.py --watchlist` commands.
- Updated version text to v1.4.

## v1.3 - Ranking & Watchlist

- Added `data/watchlist.json`.
- Added scan source arguments: `--sample` and `--watchlist`.
- Made watchlist the default scan source.
- Added ranking report at `reports/top10.md`.
- Added watchlist summary at `reports/watchlist_report.md`.
- Added price, reasonable buy point, and below-buy-point fields to scan output.

## v1.2 - Data Quality Improvement

- Added explicit scan fields for missing data and data quality.
- Added data quality score using `100 - missing_count * 5`.
- Sorted scan CSV by SAP Score and data quality score.
- Added `reports/scan_summary.md`.
- Documented scan result interpretation in README.

## v1.1 - Validation & Backtesting Foundation

- Added sample stock universe under `tests/sample_data/sample_stocks.json`.
- Added batch scan command in `scan.py`.
- Added CSV scan output at `reports/scan_results.csv`.
- Added unit tests for safe division, Piotroski, growth, valuation, and SAP Score.
- Added benchmark tracking document.
- Updated README with scan instructions.

## v1.0 - Stable Core Release

- Stabilized the core CLI workflow.
- Added project documentation in README.md.
- Documented SAP Score weight structure.
- Updated app version display to StockAnalyzerPro v1.0.
- Added gitignore rule for future Markdown reports.

## v0.9 - Growth Engine v1.0

- Added growth analysis for revenue, EPS, and free cashflow.
- Connected growth score to SAP Score.
- Updated report growth section with growth rates, scores, and notes.

## v0.8 - SAP Score Engine v1.0

- Moved SAP Score calculation into modules/scoring.py.
- Established the 100-point SAP Score category weights.
- Added detailed scoring categories and item-level reasons to reports.

## v0.7 - Valuation Engine v1.0

- Added modules/valuation.py.
- Added simplified PE/PB fair value model.
- Added dynamic buy zones and first target price.
- Added EPS and book value per share support.

## v0.6 - Complete Piotroski F-Score

- Added complete Piotroski F-Score 9-item calculation.
- Moved Piotroski logic into modules/piotroski.py.
- Updated reports with full Piotroski item details.

## v0.5 - Financial Engine v2.0

- Added current and previous financial period support.
- Added financial field alias mapping for yfinance statements.
- Added long-term debt, shares outstanding history, and diagnostics.

## v0.4 - Financial Engine v1.0

- Added FinancialData model.
- Normalized yfinance data before analysis.
- Reduced analyzer dependency on raw yfinance ticker.info.

## v0.3 - Piotroski F-Score Framework

- Added initial Piotroski F-Score structure.
- Report showed Piotroski placeholders for later completion.

## v0.2 - Fixed Report Format

- Standardized the Markdown stock analysis report structure.

## v0.1 - Initial Stock Analysis

- Added CLI stock symbol input.
- Fetched yfinance data.
- Generated an initial Markdown report.
