# Changelog

## Unreleased - FinMindProvider Completeness v3

- Expanded `FinMindProvider` balance-sheet mapping for current assets, current liabilities, long-term debt aliases, and current-ratio diagnostics.
- Added explicit `long_term_debt_missing`, `finmind_mapped_fields`, and `still_missing_fields` diagnostics so incomplete FinMind rows are visible instead of silent.
- Enhanced `CompositeProvider` to enrich successful FinMind financial data with Yahoo Finance market data, including current price, industry, sector, PE, and PB where available.
- Added PE/PB derivation from Yahoo current price plus FinMind EPS/BVPS when Yahoo PE/PB values are missing.
- Added Taiwan Chinese company-name fallback support for runtime analysis, including `6285.TW: 啟碁`.
- Updated single-stock report version text to `StockAnalyzerPro v3.0 FinMind First Beta`.
- Added unit tests for current-ratio mapping, long-term-debt alias mapping, Yahoo enrichment, PE/PB derivation, 6285 Chinese fallback, and report version regression.
- No SAP Score scoring logic, Strategy, Backtest, Historical Pipeline, or Qualification Logic changes were added.

## Unreleased - FinMind First Runtime Integration Beta

- Switched the runtime stock-data provider default from `cached_yahoo` to `composite`.
- Added `SAP_PROVIDER` environment override so users can set `SAP_PROVIDER=cached_yahoo` to return to the previous Yahoo-based flow.
- Added provider source metadata to runtime financial data diagnostics and analysis results.
- Added console and Markdown report display for provider source and fallback status.
- Added scan CSV and ranking report provider source fields.
- Added unit tests for default composite provider selection, `SAP_PROVIDER=cached_yahoo` rollback, FinMind route metadata, Yahoo fallback metadata, non-Taiwan Yahoo routing, and report provider source output.
- No SAP Score scoring logic, Analyzer scoring rules, Strategy, Backtest, Historical Pipeline, or Qualification Logic changes were added.

## Unreleased - FinMindProvider Multi-Symbol Dry Run Validation

- Added `provider_multi_dry_run.py` for safe multi-symbol provider dry-run validation before any FinMind First runtime rollout.
- Added support for watchlist, sample, and explicit symbol inputs with Markdown and CSV outputs under `reports/`.
- Added summary metrics for total count, success count, failed count, FinMind usage, Yahoo fallback usage, missing-field rows, failed rows, and runtime integration recommendation.
- Added unit tests for symbol input, watchlist source loading, sample source loading, Markdown generation, CSV generation, recommendation logic, and failure rows without crashing.
- The multi-symbol dry run does not modify downloader defaults, Analyzer, SAP Score, Strategy, Backtest, Historical Pipeline, or the historical repository.

## Unreleased - FinMindProvider Mapping Coverage v2

- Expanded `FinMindProvider` alias coverage for real FinMind XBRL-style row types, including `IncomeAfterTaxes`, `Revenue`, `GrossProfit`, `TotalAssets`, `Liabilities`, `Equity`, `OrdinaryShare`, `CashFlowsFromOperatingActivities`, `PropertyAndPlantAndEquipment`, and `EPS`.
- Added dataset-aware mapping guards so aliases with similar names are only used from the correct FinMind statement source.
- Added safer derived fields for total equity, free cash flow, EPS, and book value per share; ordinary share capital is converted into shares using Taiwan par value assumptions before EPS/BVPS derivation.
- Added mapping coverage diagnostics for `mapped_fields`, `derived_fields`, `missing_fields`, `unmapped_raw_fields`, and `provider=finmind`.
- Added dry-run display fields for `mapped_fields_count`, `derived_fields_count`, and `missing_fields_count`.
- Added unit tests for real FinMind-style aliases, derived fields, diagnostics coverage, and dry-run mapping coverage output.
- No Analyzer, Downloader runtime default, YahooFinanceProvider, SAP Score scoring logic, Strategy, Backtest, or Historical Pipeline changes were added.

## Unreleased - Fix FinMindProvider Dry Run Date Defaults

- Added safe default date ranges to `FinMindProvider.get_financial_data()`: missing dates now default to the last 3 years through today.
- Forwarded `start_date` and `end_date` to FinMind financial statement, balance sheet, and cash flow client calls.
- Converted FinMind client/API failures into `ProviderError` so `CompositeProvider` can use the existing Yahoo fallback path.
- Added `provider_dry_run.py --start` and `--end` options for explicit provider dry-run date ranges.
- Updated dry-run output to render `source_chain` with `->` for clearer fallback diagnostics.
- Added unit tests for FinMindProvider date defaults, explicit date forwarding, dry-run date argument parsing, API-error fallback, and fallback diagnostics.
- No Analyzer, Downloader runtime default, SAP Score, Strategy, Backtest, or Historical Pipeline changes were added.

## Unreleased - CompositeProvider Runtime Dry Run

- Added `provider_dry_run.py` as a safe provider diagnostics CLI for `composite`, `finmind`, and `yahoo`.
- Added dry-run output for symbol normalization, selected provider, fallback state, fallback reason, symbol type, missing-field count, source chain, and optional diagnostics.
- Added `--mock` mode for unit-testable routing diagnostics without real API calls.
- Added unit tests for CLI argument parsing, CompositeProvider Taiwan routing, fallback routing, non-Taiwan Yahoo routing, diagnostics formatting, and failure handling without crashing.
- The dry-run tool does not write reports, does not write historical repositories, does not modify downloader defaults, and is not connected to the main CLI menu.
- No Analyzer, Downloader runtime default, YahooFinanceProvider behavior, FinMindProvider mapping, Strategy, SAP Score scoring logic, Backtest, Historical Pipeline, Qualification Logic, or CLI main menu changes were added.

## Unreleased - CompositeProvider Skeleton

- Added `data_provider/providers/composite_provider.py` with an `IDataProvider`-compatible `CompositeProvider`.
- Added Taiwan stock routing that tries `FinMindProvider` first and falls back to `YahooFinanceProvider` on provider failure.
- Added direct Yahoo routing for non-Taiwan symbols and Yahoo-only routing for price history.
- Added structured routing diagnostics with primary provider, fallback provider, selected provider, fallback state, fallback reason, symbol type, and source chain.
- Registered `composite` in `ProviderFactory.with_defaults()` without changing the existing `cached_yahoo` runtime default.
- Added unit tests for FinMind primary success, Yahoo fallback, non-Taiwan routing, price-history routing, diagnostics, factory creation, and `cached_yahoo` compatibility.
- No Analyzer, Downloader runtime default, YahooFinanceProvider behavior, FinMindProvider mapping, Strategy, SAP Score scoring logic, Backtest, Historical Pipeline, Qualification Logic, or CLI changes were added.

## Unreleased - FinMindProvider Financial Mapping v1

- Implemented initial `FinMindProvider.get_financial_data()` mapping from FinMind financial statement, balance sheet, and cash flow rows into `FinancialData`.
- Added centralized field alias mapping, current/previous period selection, ROC year and quarter handling, derived equity, EPS, book value per share, and free cash flow.
- Added missing-field diagnostics on both `FinancialData.diagnostics` and provider diagnostics without crashing on partial FinMind rows.
- Updated FinMindProvider unit tests for valid mock responses, current/previous periods, long-form rows, missing fields, non-Taiwan symbols, factory creation, and `cached_yahoo` default compatibility.
- Runtime default remains unchanged; downloader and existing Yahoo/cached_yahoo analysis flows are not switched to FinMind.
- No Analyzer, Downloader runtime default, YahooFinanceProvider, Strategy, SAP Score scoring logic, Backtest, Historical Pipeline, Qualification Logic, or CLI changes were added.

## Unreleased - FinMindProvider Skeleton

- Added `data_provider/providers/finmind_provider.py` with `FinMindProvider` skeleton.
- Added provider metadata, diagnostics, Taiwan symbol detection, symbol normalization helpers, client injection, and clear placeholder behavior for unimplemented mapping and price history.
- Registered `finmind` in `ProviderFactory.with_defaults()` without changing runtime default provider selection.
- Added unit tests for factory creation, metadata, mock client injection, unsupported non-Taiwan symbols, placeholder diagnostics, symbol helpers, and `cached_yahoo` default compatibility.
- Updated README and project status to note that FinMindProvider skeleton exists but runtime analysis still uses the existing default provider.
- No Analyzer, runtime default provider, Strategy, SAP Score scoring logic, Backtest, Historical Pipeline, Qualification Logic, or CLI changes were added.

## Unreleased - FinMind First Architecture

- Added `docs/FINMIND_FIRST_ARCHITECTURE.md` for the planned `FinMind First, Yahoo Finance fallback` data-source direction.
- Documented the target `ProviderFactory -> CompositeProvider -> FinMindProvider / YahooFinanceProvider` structure.
- Defined provider priority, Taiwan / US / ETF detection rules, FinancialData mapping, cache strategy, fallback behavior, migration plan, unit test plan, Mermaid diagrams, and code review checklist.
- Updated README and project status with the next-stage data-source direction.
- No Analyzer, Provider implementation, Strategy, SAP Score scoring logic, Backtest, Historical Pipeline, Qualification Logic, or CLI changes were added.

## Unreleased - Chinese UI Localization

- Updated `app.py` to present StockAnalyzerPro v2.4 with a fully Chinese main menu and Chinese interactive prompts.
- Localized Backtest, Strategy Compare, and Research Report console output and Markdown report headings.
- Added Chinese error/help text for user-facing CLI parser descriptions where applicable.
- Added a Chinese quick-start section to README.
- Updated unit tests for localized report presentation.
- No Analyzer, Provider, Strategy, SAP Score scoring logic, Backtest strategy logic, Historical Pipeline, or Qualification Logic changes were added.

## Unreleased - v2.4 RC Validation

- Added `scripts/v2_4_rc_validation.ps1` for reproducible Historical Backtesting release-candidate validation.
- Added `v2_4_rc_validation.py` to generate `reports/v2_4_rc_validation.md` from step statuses and Backtest qualification export.
- RC validation flow imports financial snapshots, generates SAP snapshots, runs repository-sourced backtest, runs strategy comparison, and generates research report.
- RC validation report includes import status, generator status, backtest status, strategy comparison status, research report status, qualification summary, formal PIT / research-only status, and known limitations.
- Added unit tests for RC validation script flow, summary report generation, and qualification field handling.
- Updated README, project status, and CHANGELOG.
- No Analyzer, Provider, Strategy, SAP Score scoring logic, Backtest strategy logic, new strategy, new data source, GUI, or AI changes were added.

## Unreleased - Strategy Compare Qualification Integration

- Added Backtest qualification fields to `strategy_compare.py` CSV and Markdown outputs.
- Added `--snapshot-source` and `--snapshot-db` support to strategy comparison runs.
- Added Formal Point-in-Time, Research Only, and Qualification Grade display to `reports/strategy_comparison.md`.
- Updated `research_report.py` Executive Summary with formal point-in-time and research-only strategy counts.
- Added Research Only warnings to research recommendations without recalculating qualification outside Backtest output.
- Added unit tests for strategy comparison qualification integration, repository snapshot source, CSV compatibility, and research report qualification summaries.
- Updated README, project status, and CHANGELOG.
- No Analyzer, Provider, Strategy, SAP Score scoring logic, or Backtest strategy logic changes were added.

## Unreleased - Historical Backtest Qualification Export

- Added `reports/backtest_qualification.csv` and `reports/backtest_qualification.json` outputs after backtest runs.
- Added qualification export fields for snapshot source, snapshot database, qualification status, research-only counts, point-in-time counts, formal point-in-time flag, and generation timestamp.
- Preserved CSV snapshot qualification as `N/A` with `is_formal_point_in_time=false`.
- Added unit tests for CSV export, JSON export, repository formal point-in-time export, research-only export, and CSV source export.
- Updated README, Backtest README, project status, and CHANGELOG.
- No Analyzer, Provider, Strategy, SAP Score scoring logic, or Backtest strategy logic changes were added.

## Unreleased - Historical Backtest Qualification Gate

- Added Backtest qualification summary fields for repository snapshot sources.
- Added `qualification_grade`, `qualification_reason`, `research_only_count`, `point_in_time_count`, `missing_published_date_count`, and `not_point_in_time_count` to backtest results and Markdown reports.
- Added research-only report notice: `此回測僅供研究與系統驗證，不可視為正式 point-in-time 投資績效。`
- Added a Backtest qualification adapter that uses `HistoricalQualifier` for repository snapshots and preserves legacy CSV credibility behavior.
- Added unit tests for formal repository snapshots, `missing_published_date`, `not_point_in_time`, CSV compatibility, and Markdown warning output.
- Updated README, Backtest README, project status, and CHANGELOG.
- No Analyzer, Provider, Strategy, SAP Score scoring logic, or Backtest strategy logic changes were added.

## Unreleased - Historical Qualification

- Added `historical/qualification/` with `HistoricalQualifier` and `QualificationResult`.
- Added `historical_qualify.py` CLI for repository qualification reporting.
- Added `reports/historical_qualification_report.md` output support.
- Classified `missing_published_date` and `not_point_in_time` rows as research-only.
- Added unit tests for formal point-in-time qualification, research-only fallback rows, empty repositories, CLI defaults, and report generation.
- Updated README, project status, and CHANGELOG.
- No Analyzer, Provider, Strategy, SAP Score scoring logic, or Backtest strategy logic changes were added.

## Unreleased - Historical SAP Generator Incremental Update

- Added `HistoricalSAPGenerator.generate_incremental()` for affected-period rebuilds.
- Added incremental rebuild detection for missing SAP snapshots, generator version changes, and publication timeline changes.
- Added `HistoricalSnapshotRepository.get_latest_sap_snapshot_for_period()`.
- Added `--incremental` support to `historical_generate_sap.py`.
- Updated generator summaries with skipped counts, affected periods, and incremental mode.
- Added unit tests for incremental skip, old generator version rebuild, publication timeline warnings, CLI summary output, and latest SAP period lookup.
- Updated README, project status, and CHANGELOG.
- No Analyzer, Provider, Strategy, SAP Score scoring logic, or Backtest strategy logic changes were added.

## Unreleased - Historical Backtest Snapshot Source

- Added a repository snapshot read path for Backtest using `SAPScoreSnapshot` rows from `historical_snapshots.db`.
- Added `--snapshot-source csv|repository` and `--snapshot-db` CLI options while preserving CSV as the default source.
- Added `HistoricalSnapshotRepository.list_sap_snapshots()`.
- Updated `SnapshotScoreStore` to load repository snapshots and count semicolon/comma-separated warnings individually.
- Added tests for repository snapshot loading, BacktestEngine repository source loading, CLI validation, and repository SAP snapshot listing.
- Updated README, Backtest README, and project status documentation.
- No Analyzer, Provider, Strategy, SAP Score scoring logic, or Backtest strategy logic changes were added.

## Unreleased - App CLI v2.3

- Updated `app.py` to display `StockAnalyzerPro v2.3` and `Historical Pipeline MVP`.
- Reorganized the main console into stock analysis, historical data, research tools, and system sections.
- Preserved existing menu options for single-stock analysis, watchlist scan, and sample scan.
- Added console launchers for `finmind_import.py`, `historical_generate_sap.py`, `backtest.py`, `strategy_compare.py`, and `research_report.py`.
- Added `PROJECT_STATUS.md` display from the console.
- No Analyzer, Provider, Strategy, SAP Score, or Backtest core logic changes were added.

## Unreleased - Add PROJECT_STATUS

- Added `PROJECT_STATUS.md` at the project root.
- Linked the project status document from the top of `README.md`.
- Documented current version, phase, completed work, in-progress items, planned items, known limitations, test status, and next milestone.
- No program code was changed.

## v2.25 - Historical Pipeline Smoke Test

- Added `scripts/historical_pipeline_smoke_test.ps1`.
- Added end-to-end smoke flow from `tests/sample_data/historical/financial_snapshots_valid.csv` through `historical_import.py`, `HistoricalSnapshotRepository`, and `historical_generate_sap.py`.
- Added `reports/historical_pipeline_smoke_test.md` summary output.
- Added summary fields for imported financial snapshot count, generated SAP snapshot count, failed count, warning count, database path, and point-in-time status.
- Added integration test coverage for the historical pipeline and repository financial/SAP snapshot checks.
- No SAP Score scoring logic, Analyzer, Provider, Backtest, or Strategy changes were added.

## v2.24 - Historical SAP Generator CLI

- Added `historical_generate_sap.py`.
- Added CLI arguments for `--db`, `--symbol`, `--year`, and `--quarter`.
- Added filtered generation for symbol, fiscal year, and fiscal quarter.
- Added summary output with database path, generated count, updated count, failed count, warning count, and filters used.
- Updated `reports/historical_generator_summary.md` to include database and filter fields.
- Added unit tests for default CLI args, symbol filtering, year/quarter filtering, summary generation, and repository SAP snapshot writes.
- No Backtest, Strategy, Analyzer, Provider, or SAP Score scoring logic changes were added.

## v2.23 - Historical SAP Generator MVP

- Added `historical/sap_generator.py`.
- Added `HistoricalSAPGenerator.generate_snapshot()` for converting one `FinancialStatementSnapshot` into one `SAPScoreSnapshot`.
- Added `HistoricalSAPGenerator.generate_all()` for rebuilding SAP score snapshots from all repository financial statement snapshots.
- Reused the existing analyzer/SAP scoring path instead of reimplementing SAP Score logic.
- Updated `HistoricalSnapshotRepository.insert_sap_snapshot()` to update an existing `(symbol, fiscal_year, fiscal_quarter)` snapshot.
- Added `HistoricalSnapshotRepository.list_financial_snapshots()`.
- Added `reports/historical_generator_summary.md`.
- Added unit tests for single snapshot generation, multiple snapshot generation, duplicate update, and repository integration.
- No Backtest, Strategy, Analyzer, Provider, or SAP Score scoring logic changes were added.

## Unreleased - Document FinMind Smoke Test Result

- Documented the real FinMind smoke test result for `2330` from `2024-01-01` to `2024-12-31`.
- Recorded `imported_count=68`, `failed_count=0`, `warning_count=132`, and SQLite row count `68`.
- Clarified that the main warning is `missing_published_date`.
- Clarified that missing published-date fallback rows are stored with `is_point_in_time=false`.
- Documented that FinMind financial statements can currently be imported successfully, but rows without announcement dates are not formal point-in-time data.
- No program code was changed.

## Unreleased - Fix FinMind Missing Published Date Fallback

- Fixed FinMind financial statement mapping when API rows do not include `published_date`, `release_date`, or `filing_date`.
- Added fallback from missing published date to `statement_date` / `date`.
- Marked fallback rows with `warning=missing_published_date` and `is_point_in_time=false`.
- Updated historical validation to allow fallback rows while recording a clear warning.
- Added tests for mapper fallback, validator warnings, importer repository writes, and official published-date point-in-time behavior.
- Updated the FinMind smoke test guide to explain that fallback rows are not formal point-in-time records.
- No analyzer changes, SAP Score changes, backtest changes, strategy changes, provider changes, FinMindClient request logic changes, or FinMindImporter flow changes were added.

## v2.22 - FinMind Smoke Test Guide

- Added `docs/FINMIND_SMOKE_TEST.md`.
- Added `scripts/finmind_smoke_test.ps1`.
- Documented safe real-API smoke testing with `FINMIND_TOKEN`.
- Documented the recommended smoke test symbol `2330` and date range `2024-01-01` to `2024-12-31`.
- Documented use of `historical_snapshots_test.db` and warned against writing smoke test data to `historical_snapshots.db`.
- Documented how to review `reports/finmind_import_summary.md`, confirm SQLite row counts, and delete the test database.
- Updated README with the smoke test guide and helper script entry point.
- No analyzer changes, provider changes, backtest changes, strategy changes, SAP Score changes, FinMindClient changes, or FinMindImporter changes were added.

## v2.21 - FinMind Import CLI

- Added `finmind_import.py`.
- Added CLI arguments for `--symbol`, `--start`, `--end`, `--db`, and `--token`.
- Added `FINMIND_TOKEN` fallback when `--token` is not provided.
- Added `FinMindImporter.import_financial_statements()` CLI flow into `HistoricalSnapshotRepository`.
- Added `reports/finmind_import_summary.md` output with symbol, date range, import counts, errors, warnings, and repository path.
- Added unit tests for CLI argument parsing, token resolution from environment, missing symbol errors, and mock importer summary generation.
- Documented token behavior and anonymous access limitations in README.
- No analyzer changes, provider changes, backtest changes, strategy changes, SAP Score changes, or FinMindClient request logic changes were added.

## v2.20 - FinMind Importer Integration

- Integrated `FinMindImporter.import_financial_statements()` with `FinMindClient.get_financial_statement()`.
- Added financial statement row mapping through `map_financial_statement_row()`.
- Added validation through `HistoricalValidator.validate_financial_snapshot()`.
- Added valid financial snapshot writes through `HistoricalSnapshotRepository.insert_financial_snapshot()`.
- Added `ImportResult` error handling for invalid rows, mapping failures, validation failures, repository write failures, and FinMind API errors.
- Added warning-preserving import behavior for validation warnings.
- Added mock-client unit tests for valid import, invalid row rejection, warning-preserving import, and API error conversion.
- SAP score snapshot import from FinMind remains unimplemented.
- No analyzer changes, provider changes, backtest changes, strategy changes, SAP Score changes, or FinMindClient request logic changes were added.

## v2.19 - FinMind API Request Methods

- Added `FinMindClient.get_financial_statement()`.
- Added `FinMindClient.get_balance_sheet()`.
- Added `FinMindClient.get_cash_flow()`.
- Routed FinMind dataset requests through `_request()`.
- Added query param construction for dataset, stock ID, optional date range, and optional token.
- Added timeout and retry handling through `FinMindConfig`.
- Added normalized handling for HTTP errors, rate limits, and authentication errors.
- Added mock-session unit tests for success, HTTP error, rate limit, auth error, retry success, and request validation.
- No repository writes, FinMindImporter import flow, analyzer changes, provider changes, backtest changes, SAP Score changes, or mapper changes were added.

## v2.18 - FinMind API Mapping

- Added `importers/finmind/mappers.py`.
- Added `map_financial_statement_row()` for converting FinMind-style dict rows to `FinancialStatementSnapshot`.
- Added `map_sap_snapshot_row()` for converting FinMind-style dict rows to `SAPScoreSnapshot`.
- Added `FinMindMappingError` for clear missing-field and invalid mapping errors.
- Added Republic of China year conversion, fiscal quarter mapping, symbol normalization, and FinMind source metadata.
- Added unit tests for valid financial rows, valid SAP rows, missing required fields, date conversion, and quarter mapping.
- No FinMind API calls, repository changes, analyzer changes, provider changes, backtest changes, or SAP Score changes were added.

## v2.17 - Architecture Consolidation

- Added `docs/ARCHITECTURE_OVERVIEW.md`.
- Consolidated project layer diagram, dependency rules, module responsibilities, directory structure, extension points, and code review checklist.
- Documented Provider, Strategy, Historical, Import, Validation, Cache, and Research framework responsibilities.
- Added an allowed import matrix to protect dependency direction before future FinMind, OpenBB, and Polygon work.
- Updated README with the Architecture Overview entry point.
- No runtime features, analyzer, provider, importer, repository, backtest, SAP Score, historical module, or strategy behavior changed.

## v2.16 - FinMind API Client

- Added `importers/finmind/`.
- Added `FinMindConfig` with base URL, token, timeout, and max retry settings.
- Added `FinMindClient` with config storage, session creation, optional token header management, and request method placeholders.
- Added FinMind exception hierarchy.
- Added `FinMindResponse` API response dataclass.
- Updated `FinMindImporter` to own a `FinMindClient` while leaving import methods unimplemented.
- Added unit tests for client initialization, config defaults, exception hierarchy, response model, and importer client wiring.
- No API calls, repository changes, snapshot changes, analyzer changes, SAP Score changes, or FinMind import flow implementation was added.

## v2.15 - FinMind Importer Architecture

- Added `importers/finmind_importer.py`.
- Added architecture-only `FinMindImporter` with metadata, `supports()`, `import_snapshot()`, and `import_financial_statements()`.
- Registered `finmind` in the default `ImporterRegistry`.
- Added `docs/FINMIND_IMPORTER_ARCHITECTURE.md` with API mapping, financial statement mapping, quarter mapping, snapshot flow, rate limit, retry, error handling, point-in-time considerations, diagrams, and migration plan.
- Added unit tests for default registry registration, importer metadata, and supported snapshot types.
- Documented planned data sources in README.
- No network calls, API implementation, repository writes, analyzer, provider, strategy, backtest, or SAP Score behavior changed.

## v2.14 - Data Quality Profiling

- Added `historical/profiling/`.
- Added `ProfileResult` with row counts, warning counts, duplicate counts, missing-field metrics, point-in-time metrics, and quality score.
- Added `HistoricalProfiler.profile_import()` and `HistoricalProfiler.profile_repository()`.
- Added centralized quality metrics in `historical/profiling/metrics.py`.
- Added `reports/data_quality_report.md`.
- Added unit tests for quality score calculation, missing percentage, duplicate statistics, point-in-time percentage, empty repository profiling, and report generation.
- No analyzer, provider, strategy, backtest, SAP Score, historical repository, or historical validator behavior changed.

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
