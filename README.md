# StockAnalyzerPro

StockAnalyzerPro is a Python CLI stock analysis project for personal investment research. It focuses on producing a repeatable Markdown report from a fixed investment logic, rather than only fetching market data.

Current version: v1.3 Ranking & Watchlist

## Current Features

- Fetches stock and financial data with yfinance.
- Normalizes raw data into FinancialData and FinancialPeriod models.
- Generates a fixed-format Markdown stock analysis report.
- Calculates complete Piotroski F-Score 9 items.
- Calculates SAP Score with a 100-point weighted scoring engine.
- Includes profitability, financial health, cashflow, valuation, and growth analysis.
- Estimates simplified valuation, buy zones, and first target price.
- Shows diagnostics when required financial fields are missing.
- Provides a validation scan over a sample stock universe and exports CSV results.

## Installation

Create and activate the Python virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run

Start the CLI:

```powershell
python app.py
```

Or run directly with the project virtual environment:

```powershell
.venv\Scripts\python.exe app.py
```

When prompted:

- Enter a stock symbol, for example `2330`.
- Enter `q` to exit.

Reports are generated in the `reports/` folder.

## Batch Scan

Run the default watchlist scan:

```powershell
.venv\Scripts\python.exe scan.py
```

Run the sample universe scan:

```powershell
.venv\Scripts\python.exe scan.py --sample
```

Run the watchlist scan explicitly:

```powershell
.venv\Scripts\python.exe scan.py --watchlist
```

The sample scan reads:

```text
tests/sample_data/sample_stocks.json
```

The watchlist scan reads:

```text
data/watchlist.json
```

The CSV output is written to:

```text
reports/scan_results.csv
```

The scan result includes SAP Score, Piotroski F-Score, fair price, first target price, diagnostics count, runtime, and per-symbol error messages when analysis fails.

v1.2 scan output also includes:

- `missing_count`: number of missing normalized financial fields.
- `missing_fields`: the missing field names.
- `data_quality_score`: `100 - missing_count * 5`, with a minimum of 0.
- `piotroski_available`: number of Piotroski items that can be calculated.
- `valuation_available`: number of valuation base prices available.
- `growth_available`: number of growth rates available.

The CSV is sorted by SAP Score from high to low, then data quality score from high to low.

The scan also writes a summary report:

```text
reports/scan_summary.md
```

Additional ranking reports:

```text
reports/top10.md
reports/watchlist_report.md
```

Use the summary to review total sample count, success rate, average SAP Score, average data quality score, the stocks with the most missing data, and the top 10 SAP Score stocks. Use the watchlist report to review SAP Score, grade, whether price is below the reasonable buy point, first target price, and data quality for your selected stocks.

## Notes

- This project is for research and learning, not investment advice.
- Data quality depends on yfinance availability.
- Future versions may add additional data sources and backtesting workflows, but v1.3 keeps the ranking and watchlist workflow simple.
