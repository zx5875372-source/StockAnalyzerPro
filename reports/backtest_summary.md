# Backtest Summary

Version: Sprint 3 Backtest Engine MVP

## Config

| Item | Value |
|---|---:|
| Start Date | 2023-01-01 |
| End Date | 2025-12-31 |
| Initial Cash | 1000000 |
| Rebalance | Monthly |
| Universe | tests\sample_data\sample_stocks.json |

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
| Total Return | 213.36% |
| CAGR | 46.34% |
| Max Drawdown | -19.63% |
| Win Rate | 63.89% |
| Sharpe | TODO |
| Sortino | TODO |

## Selected Symbols

- 2330.TW

## Diagnostics

- 無

## Notes

This MVP uses the current SAP Score snapshot with historical price data. It is
not yet a look-ahead-safe historical financial statement backtest.
