# Historical Import CSV Format

This document describes the CSV files accepted by `historical_import.py`.

The importer currently supports:

- SAP score snapshots with `--type sap`
- Financial statement snapshots with `--type financial`

The importer validates every row before writing to `HistoricalSnapshotRepository`.

## SAP Snapshot CSV

Required columns:

```text
symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,sap_score,piotroski_score,data_quality_score,credibility_grade,warning
```

Example:

```csv
symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,sap_score,piotroski_score,data_quality_score,credibility_grade,warning
1101,2024,4,2024-12-31,2025-03-20,2025-03-21,sample_fixture,v1,true,2025-03-21T00:00:00+00:00,82,7,95,A,
```

Validation rules:

- `symbol` is required. Numeric Taiwan symbols are normalized to `.TW`.
- `fiscal_year` must be an integer greater than or equal to 1900.
- `fiscal_quarter` must be `1`, `2`, `3`, or `4`.
- `published_date` and `snapshot_date` must use `YYYY-MM-DD`.
- `published_date` must be on or before `snapshot_date`.
- `is_point_in_time` must be a boolean value such as `true` or `false`.
- `sap_score` must be between `0` and `100`.
- `piotroski_score` must be between `0` and `9`.
- `data_quality_score` must be between `0` and `100`.
- `credibility_grade` must be `A`, `B`, `C`, or `D`.

## Financial Snapshot CSV

Required columns:

```text
symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,statement_type,payload_json,warning
```

Example:

```csv
symbol,fiscal_year,fiscal_quarter,statement_date,published_date,snapshot_date,source,source_version,is_point_in_time,created_at,statement_type,payload_json,warning
1101,2024,4,2024-12-31,2025-03-20,2025-03-21,sample_fixture,v1,true,2025-03-21T00:00:00+00:00,income_statement,"{""revenue"": 280000000000}",
```

Validation rules:

- `symbol` is required. Numeric Taiwan symbols are normalized to `.TW`.
- `fiscal_year` must be an integer greater than or equal to 1900.
- `fiscal_quarter` must be `1`, `2`, `3`, or `4`.
- `published_date` and `snapshot_date` must use `YYYY-MM-DD`.
- `published_date` must be on or before `snapshot_date`.
- `is_point_in_time` must be a boolean value such as `true` or `false`.
- `statement_type` is required.
- `payload_json` is stored as text in this MVP.

## Sample Files

Valid samples:

```powershell
.venv\Scripts\python.exe historical_import.py --type sap --file tests/sample_data/historical/sap_snapshots_valid.csv
.venv\Scripts\python.exe historical_import.py --type financial --file tests/sample_data/historical/financial_snapshots_valid.csv
```

Invalid samples:

```powershell
.venv\Scripts\python.exe historical_import.py --type sap --file tests/sample_data/historical/sap_snapshots_invalid.csv
.venv\Scripts\python.exe historical_import.py --type financial --file tests/sample_data/historical/financial_snapshots_invalid.csv
```

## Common Errors

- Missing required columns: the CSV header does not include all required fields.
- Missing required field values: a required cell is blank.
- Invalid date format: dates must use `YYYY-MM-DD`.
- Invalid date order: `published_date` is later than `snapshot_date`.
- Invalid quarter: `fiscal_quarter` is outside `1` to `4`.
- Invalid score range: SAP, Piotroski, or data quality scores are outside valid ranges.
- Invalid credibility grade: grade is not `A`, `B`, `C`, or `D`.
- Duplicate SAP rows: the repository has a unique constraint for SAP snapshots with the same symbol, fiscal period, snapshot date, source, and source version.

## Failed vs Warning

Validation failed:

- The row is not written to `HistoricalSnapshotRepository`.
- `failed_count` increases.
- The row-level reason appears in `errors`.

Validation warning:

- The row is still written to `HistoricalSnapshotRepository`.
- `warning_count` increases.
- The row-level warning appears in `warnings`.

The first warning currently implemented is duplicate-key detection within the import batch. It helps flag repeated snapshot identity rows before later point-in-time pipelines depend on them.
