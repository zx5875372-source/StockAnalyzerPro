# Changelog

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
