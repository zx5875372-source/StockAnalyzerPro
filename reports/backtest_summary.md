# Backtest Summary

Version: Sprint 4 Backtest Data Integrity

## Config

| Item | Value |
|---|---:|
| Start Date | 2023-01-01 |
| End Date | 2025-12-31 |
| Initial Cash | 1000000 |
| Rebalance | Monthly |
| Universe | tests\sample_data\sample_stocks.json |
| Snapshot Source | data\snapshots\sample_sap_scores.csv |
| Look-ahead-safe | true |

## Strategy

| Item | Value |
|---|---:|
| Strategy | SAP Score Strategy MVP |
| SAP Score >= | 80 |
| Piotroski >= | 7 |
| Data Quality >= | 80 |

## Performance

| Metric | Value |
|---|---:|
| Total Return | 161.55% |
| CAGR | 37.78% |
| Max Drawdown | -8.70% |
| Win Rate | 61.11% |
| Sharpe | TODO |
| Sortino | TODO |

## Data Integrity

| Item | Value |
|---|---:|
| Snapshot Source | data\snapshots\sample_sap_scores.csv |
| Look-ahead-safe | true |
| Selected Stock Count | 2 |
| Skipped Stock Count | 28 |

## Selected Symbols

- 2330.TW
- 2303.TW

## Skipped Reasons

- 0050.TW: no snapshot on or before 2025-12-31
- 0056.TW: no snapshot on or before 2025-12-31
- 006208.TW: no snapshot on or before 2025-12-31
- 00713.TW: no snapshot on or before 2025-12-31
- 00878.TW: no snapshot on or before 2025-12-31
- 00919.TW: no snapshot on or before 2025-12-31
- 1216.TW: no snapshot on or before 2025-12-31
- 1301.TW: no snapshot on or before 2025-12-31
- 1303.TW: no snapshot on or before 2025-12-31
- 2002.TW: no snapshot on or before 2025-12-31
- 2207.TW: no snapshot on or before 2025-12-31
- 2313.TW: no snapshot on or before 2025-12-31
- 2368.TW: no snapshot on or before 2025-12-31
- 2379.TW: no snapshot on or before 2025-12-31
- 2454.TW: sap_score 79 < 80
- 2603.TW: no snapshot on or before 2025-12-31
- 2881.TW: no snapshot on or before 2025-12-31
- 2882.TW: no snapshot on or before 2025-12-31
- 2884.TW: no snapshot on or before 2025-12-31
- 2885.TW: no snapshot on or before 2025-12-31
- 2891.TW: no snapshot on or before 2025-12-31
- 2892.TW: no snapshot on or before 2025-12-31
- 2912.TW: no snapshot on or before 2025-12-31
- 3034.TW: no snapshot on or before 2025-12-31
- 3037.TW: no snapshot on or before 2025-12-31
- 3189.TW: no snapshot on or before 2025-12-31
- 3711.TW: no snapshot on or before 2025-12-31
- 8046.TW: no snapshot on or before 2025-12-31

## Diagnostics

- 無

## Notes

This MVP uses historical SAP Score snapshots from the configured snapshot source.
It does not fallback to current scores. The sample snapshot file is still a
simplified fixture and not a complete point-in-time financial statement dataset.
