# Benchmark

Version: v1.2 Data Quality Improvement

This file records the validation baseline for the current core engine. Use `scan.py` to generate `reports/scan_results.csv`, then update these numbers when running a fresh benchmark.

## Baseline Command

```powershell
.venv\Scripts\python.exe scan.py
```

## Metrics

| Metric | Value |
|---|---:|
| Sample size | 30 |
| Successful analyses | 30 |
| Failed analyses | 0 |
| Success rate | 100.0% |
| Total runtime | 23.94 seconds |
| Average runtime per stock | 0.8 seconds |
| Stocks with diagnostics | 7 |
| Missing-data ratio | 23.33% |

## Notes

- The sample universe is stored in `tests/sample_data/sample_stocks.json`.
- The scan output is written to `reports/scan_results.csv`.
- Results may vary depending on yfinance response quality and network speed.
