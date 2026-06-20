# Backtest Summary

Version: Sprint 7 Benchmark Comparison

## Config

| Item | Value |
|---|---:|
| Start Date | 2023-01-01 |
| End Date | 2025-12-31 |
| Initial Cash | 1000000 |
| Rebalance | Monthly |
| Benchmark | 0050.TW |
| Universe | tests\sample_data\sample_stocks.json |
| Snapshot Source | data\snapshots\generated_sap_scores.csv |
| Look-ahead-safe | true |
| Snapshot Point-in-time | false |

## Credibility

| Item | Value |
|---|---|
| Credibility Grade | D |
| Credibility Reason | 入選股票數 1 低於最低門檻 2。 |

此結果僅供系統測試，不可作為投資策略績效依據。

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
| Total Return | 205.24% |
| CAGR | 45.06% |
| Max Drawdown | -19.63% |
| Win Rate | 61.11% |
| Sharpe | TODO |
| Sortino | TODO |

## Benchmark Comparison

| Metric | Value |
|---|---:|
| Strategy Total Return | 205.24% |
| Strategy CAGR | 45.06% |
| Benchmark | 0050.TW |
| Benchmark Total Return | 158.12% |
| Benchmark CAGR | 37.17% |
| Excess Return | 47.12% |
| Excess CAGR | 7.89% |
| Strategy vs Benchmark | 是 |

## Data Integrity

| Item | Value |
|---|---:|
| Snapshot Source | data\snapshots\generated_sap_scores.csv |
| Look-ahead-safe | true |
| Snapshot Point-in-time | false |
| Selected Stock Count | 1 |
| Skipped Stock Count | 29 |

## Snapshot Warnings

| Warning | Count |
|---|---:|
| not_point_in_time | 360 |

## Selected Symbols

- 2330.TW

## Skipped Reasons

- 0050.TW: sap_score 0 < 80; piotroski_score 0 < 7
- 0056.TW: sap_score 0 < 80; piotroski_score 0 < 7
- 006208.TW: sap_score 0 < 80; piotroski_score 0 < 7
- 00713.TW: sap_score 0 < 80; piotroski_score 0 < 7
- 00878.TW: sap_score 0 < 80; piotroski_score 0 < 7
- 00919.TW: sap_score 0 < 80; piotroski_score 0 < 7
- 1216.TW: sap_score 44 < 80; piotroski_score 6 < 7
- 1301.TW: sap_score 39 < 80; piotroski_score 4 < 7
- 1303.TW: sap_score 48 < 80
- 2002.TW: sap_score 42 < 80; piotroski_score 4 < 7
- 2207.TW: sap_score 56 < 80; piotroski_score 5 < 7
- 2303.TW: sap_score 62 < 80; piotroski_score 5 < 7
- 2313.TW: sap_score 76 < 80
- 2368.TW: sap_score 67 < 80; piotroski_score 5 < 7
- 2379.TW: sap_score 58 < 80; piotroski_score 3 < 7
- 2454.TW: sap_score 66 < 80; piotroski_score 4 < 7
- 2603.TW: sap_score 65 < 80; piotroski_score 4 < 7
- 2881.TW: sap_score 51 < 80; piotroski_score 4 < 7; data_quality_score 70 < 80
- 2882.TW: sap_score 54 < 80; piotroski_score 5 < 7; data_quality_score 70 < 80
- 2884.TW: sap_score 59 < 80; piotroski_score 6 < 7; data_quality_score 70 < 80
- 2885.TW: sap_score 28 < 80; piotroski_score 3 < 7
- 2891.TW: sap_score 60 < 80; piotroski_score 4 < 7; data_quality_score 70 < 80
- 2892.TW: sap_score 51 < 80; piotroski_score 4 < 7; data_quality_score 70 < 80
- 2912.TW: sap_score 48 < 80; piotroski_score 6 < 7
- 3034.TW: sap_score 65 < 80; piotroski_score 5 < 7
- 3037.TW: sap_score 58 < 80
- 3189.TW: sap_score 59 < 80; piotroski_score 6 < 7
- 3711.TW: sap_score 54 < 80; piotroski_score 6 < 7
- 8046.TW: sap_score 69 < 80

## Diagnostics

- 無

## Notes

This MVP uses historical SAP Score snapshots from the configured snapshot source.
It does not fallback to current scores during backtest selection. Generated
snapshots marked `current_analysis_proxy` and `not_point_in_time` are proxy data,
not formal point-in-time financial statement snapshots.
