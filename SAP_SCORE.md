# SAP Score

Current version: SAP Score Engine v1.0

The SAP Score is a 100-point scoring framework used by StockAnalyzerPro. It is designed to be explainable, repeatable, and easy to revise as the project grows.

## Weight Structure

| Category | Max Score |
|---|---:|
| Piotroski F-Score | 27 |
| Profitability | 20 |
| Financial Health | 15 |
| Cashflow | 15 |
| Valuation | 10 |
| Growth | 13 |
| Total | 100 |

## Category Details

### Piotroski F-Score - 27 points

- 9 items total.
- Each passed item adds 3 points.
- Missing data does not add points.

### Profitability - 20 points

- ROE: max 12 points.
- ROA: max 8 points.

### Financial Health - 15 points

- Debt-to-equity: max 8 points.
- Current ratio: max 7 points.

### Cashflow - 15 points

- Operating cashflow greater than 0: 7 points.
- Free cashflow greater than 0: 8 points.

### Valuation - 10 points

- PE less than 15: 5 points.
- PB less than 2: 5 points.
- Missing PE or PB data does not add points.

### Growth - 13 points

- Revenue growth: max 5 points.
- EPS growth: max 5 points.
- Free cashflow growth: max 3 points.

## Grade Mapping

| Score | Grade |
|---:|---|
| 90-100 | S |
| 80-89 | A |
| 70-79 | B |
| 60-69 | C |
| 0-59 | D |
