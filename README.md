# StockAnalyzerPro

StockAnalyzerPro is a Python CLI stock analysis project for personal investment research. It focuses on producing a repeatable Markdown report from a fixed investment logic, rather than only fetching market data.

Current version: v1.1 Validation & Backtesting Foundation

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

Run the validation scan against the sample stock universe:

```powershell
.venv\Scripts\python.exe scan.py
```

The scan reads:

```text
tests/sample_data/sample_stocks.json
```

The CSV output is written to:

```text
reports/scan_results.csv
```

The scan result includes SAP Score, Piotroski F-Score, fair price, first target price, diagnostics count, runtime, and per-symbol error messages when analysis fails.

## Notes

- This project is for research and learning, not investment advice.
- Data quality depends on yfinance availability.
- Future versions may add additional data sources and backtesting workflows, but v1.1 keeps the validation foundation simple.
