# Changelog

## v2.13 - Historical Import Fixtures

- Added reusable historical import sample CSV files under `tests/sample_data/historical/`.
- Added valid and invalid SAP snapshot CSV fixtures.
- Added valid and invalid financial statement snapshot CSV fixtures.
- Added `docs/HISTORICAL_IMPORT_FORMAT.md` with SAP and financial CSV formats, required fields, common errors, and validation failure versus warning behavior.
- Updated README with direct `historical_import.py` sample commands.
- Added unit tests for valid sample imports, invalid sample failures, and summary report generation.
- No analyzer, provider, backtest, strategy, SAP Score, or API acquisition behavior changed.

## v2.12 - Historical Import CLI

- Added `historical_import.py`.
- Added CLI arguments `--type sap`, `--type financial`, `--file`, and `--db`.
- Uses `CSVHistoricalImporter` with `HistoricalValidator` before writing snapshots.
- Writes valid `SAPScoreSnapshot` and `FinancialStatementSnapshot` rows into `HistoricalSnapshotRepository`.
- Outputs `reports/historical_import_summary.md` with imported count, failed count, warning count, errors, and warnings.
- Added unit tests for successful SAP import, invalid CSV failure, warning-preserving import, summary output, and missing file errors.
- No analyzer, provider, backtest, strategy, SAP Score, or API acquisition behavior changed.

## v2.11 - Validation Integration

- Integrated `HistoricalValidator` into `CSVHistoricalImporter`.
- CSV rows are validated before being added to imported snapshot results.
- Validation failures are excluded from imported snapshots, increment `failed_count`, and record clear row-level errors.
- Validation warnings are recorded in `ImportResult.warnings` while still allowing the snapshot to import.
- Added unit tests for valid CSV import, missing required field validation, invalid score validation, and warning-preserving import.
- No analyzer, provider, backtest, strategy, SAP Score, API acquisition, or repository behavior changed.

## v2.10 - Historical Validation Framework

- Added `historical/validation/`.
- Added `ValidationResult` with `is_valid`, `errors`, `warnings`, `field_count`, and `missing_fields`.
- Added `HistoricalValidator` for validating `FinancialStatementSnapshot` and `SAPScoreSnapshot`.
- Added validation rules for symbols, snapshot dates, published dates, fiscal periods, SAP Score, Piotroski Score, data quality score, credibility grade, point-in-time flags, and duplicate snapshot warnings.
- Added a reserved `validator` hook to `CSVHistoricalImporter` without changing the CSV import flow.
- Added unit tests for valid snapshots, missing fields, invalid dates, score ranges, duplicate warnings, and the importer validation hook.
- No analyzer, provider, backtest, strategy, SAP Score, repository, API acquisition, or real data import behavior changed.

## v2.9 - Historical Import Framework

- Added the initial `importers/` package.
- Added `BaseImporter` with `supports()`, `import_snapshot()`, `import_financial_statements()`, `name`, and `version`.
- Added `ImportResult` for normalized import counts, imported snapshots, and row-level errors.
- Added `ImporterRegistry` with register, unregister, get, and list support.
- Added `MockImporter` for deterministic unit tests.
- Added `CSVHistoricalImporter` for CSV import of `FinancialStatementSnapshot` and `SAPScoreSnapshot`.
- Added unit tests for registry behavior, duplicate registration errors, mock imports, and CSV historical imports.
- No analyzer, provider, backtest, strategy, SAP Score, Snapshot Generator, Historical Repository, or real data acquisition behavior changed.

## v2.8 - Snapshot Generator MVP

- Added `historical/generator.py`.
- Added `SnapshotGenerator` for writing current analyzer proxy SAP Score snapshots into `HistoricalSnapshotRepository`.
- Added `snapshot_repository_builder.py` to read `tests/sample_data/sample_stocks.json`, run the existing analyzer flow, and write repository snapshots.
- Outputs `reports/snapshot_repository_summary.md`.
- Marks generated repository snapshots with `source=current_analysis_proxy`, `source_version=v0`, `is_point_in_time=false`, and `warning=not_point_in_time`.
- Only `SAPScoreSnapshot` rows are written; `FinancialStatementSnapshot` generation is deferred.
- Added unit tests for generator output, proxy warning, and repository query behavior.
- No analyzer, provider, SAP Score, or backtest behavior changed.

## v2.7 - Historical Snapshot Repository

- Added `historical/repository.py`.
- Added `HistoricalSnapshotRepository` for initializing schema, inserting financial snapshots, inserting SAP score snapshots, querying snapshots, listing snapshot dates, and listing symbols.
- Uses `historical_snapshots.db` by default and creates schema on first use.
- Added unit tests for schema initialization, inserts, queries, date listing, and symbol listing.
- No analyzer, provider, backtest, SAP Score, generator, or historical data fetching behavior changed.

## v2.6 - Historical Snapshot Schema

- Added initial `historical/` package for point-in-time snapshot infrastructure.
- Added `FinancialStatementSnapshot`, `SAPScoreSnapshot`, and `SnapshotMetadata` dataclasses.
- Added SQLite schema strings for `financial_statement_snapshots`, `sap_score_snapshots`, and `snapshot_metadata`.
- Added unit tests for dataclass creation, required tables, and point-in-time fields.
- No analyzer, provider, backtest, or data fetching behavior changed.

## v2.5 - Research Report Engine

- Added `research_report.py` to generate a Markdown research report from `reports/strategy_comparison.csv`.
- Outputs `reports/research_report.md`.
- Added executive summary, strategy ranking, risk comparison, credibility analysis, and recommendation sections.
- Recommendation explicitly marks C/D credibility results as research-only and not formal investment performance.
- Added unit tests for CSV loading, Markdown generation, and empty CSV errors.

## v2.4 - Strategy Comparison Report

- Added `strategy_compare.py` for running multiple strategies with the same backtest parameters.
- Supports `--start`, `--end`, `--capital`, `--benchmark`, `--snapshot`, `--universe`, and `--strategies`.
- Outputs `reports/strategy_comparison.md` and `reports/strategy_comparison.csv`.
- Sorts comparison rows by credibility grade, then excess return.
- Added unit tests for two-strategy comparison, unknown strategy errors, and CSV/Markdown report generation.

## v2.3 - Piotroski Strategy Implementation

- Added `strategy/piotroski_strategy.py` as the second formal strategy.
- Registered both `sap` and `piotroski` in the default `StrategyRegistry`.
- Added `backtest.py --strategy` with supported values `sap` and `piotroski`.
- Backtest summaries now include the active strategy in the config section.
- Added unit tests for Piotroski strategy selection, strategy CLI creation, and strategy registry defaults.

## v2.2 - Strategy Registry Implementation

- Added formal `strategy/` package with `BaseStrategy`, `StrategyResult`, and `StrategyRegistry`.
- Moved current SAP Score backtest strategy into `strategy/sap_strategy.py` without changing threshold behavior.
- Updated `BacktestEngine` to depend on the formal `strategy.base_strategy.BaseStrategy`.
- Kept `backtest/strategy.py` as a compatibility re-export for existing imports.
- Added unit tests for strategy registration, duplicate registration, lookup, listing, unregister, and SAP strategy execution.

## Sprint 8 - Backtest CLI Options

- Added CLI options to `backtest.py`: `--start`, `--end`, `--capital`, `--benchmark`, `--snapshot`, and `--universe`.
- Added argument validation for date order, positive capital, snapshot path, and universe path.
- Backtest reports now reflect the exact parameters used for each run.
- Added unit tests for default arguments, custom benchmark, invalid capital, and invalid date order.

## Sprint 7 - Benchmark Comparison

- Added default benchmark setting `0050.TW`.
- Backtest now loads benchmark historical prices with the same date range.
- Added benchmark total return, benchmark CAGR, excess return, excess CAGR, and strategy-vs-benchmark status.
- Backtest report now includes a benchmark comparison section.
- Benchmark unavailable cases no longer crash and are recorded in diagnostics.
- Added unit tests for benchmark calculation, missing benchmark handling, and excess return.

## Sprint 6 - Backtest Report Integrity

- Added backtest credibility grading.
- Added credibility reason and low-credibility warning text to backtest reports.
- Added snapshot point-in-time status to backtest summaries.
- Moved credibility calculation out of the report layer.
- Added unit tests for credibility grades A, C, and D.

## Sprint 5 - Snapshot Builder

- Added `snapshot_builder.py`.
- Generates quarterly proxy SAP Score snapshots from `tests/sample_data/sample_stocks.json`.
- Outputs `data/snapshots/generated_sap_scores.csv`.
- Adds `source=current_analysis_proxy` and `warning=not_point_in_time` to generated rows.
- Backtest now prefers generated snapshots and falls back to sample snapshots.
- Backtest report now includes snapshot warning statistics.
- Added unit tests for snapshot builder output, proxy warnings, and generated snapshot loading.

## Sprint 4 - Backtest Data Integrity

- Added historical SAP Score snapshot fixture at `data/snapshots/sample_sap_scores.csv`.
- Added snapshot loading layer for point-in-time score lookup.
- Updated `SAPScoreStrategy` to use only the latest snapshot on or before each rebalance date.
- Removed current score fallback from the backtest selection path.
- Added skipped stock reasons, selected/skipped counts, snapshot source, and look-ahead-safe flag to backtest reports.
- Added unit tests for future snapshot prevention, missing snapshot skips, and no current-score fallback.
- Documented that Sprint 3 results should not be treated as formal backtest performance.

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
