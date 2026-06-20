import pandas as pd
import yfinance as yf

from models.financial_data import FinancialData


def normalize_symbol(symbol: str) -> str:
    symbol = symbol.strip()

    if symbol.endswith(".TW") or symbol.endswith(".TWO"):
        return symbol

    if symbol.isdigit():
        return symbol + ".TW"

    return symbol


def safe_info_get(info: dict, key: str, default=None):
    value = info.get(key, default)
    return value if value is not None else default


def normalize_number(value):
    if value is None or pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def latest_statement_value(statement, row_names: list[str]):
    if statement is None or statement.empty:
        return None

    index_lookup = {str(index).lower(): index for index in statement.index}

    for row_name in row_names:
        matched_index = index_lookup.get(row_name.lower())
        if matched_index is None:
            continue

        row = statement.loc[matched_index]
        if isinstance(row, pd.DataFrame):
            row = row.iloc[0]

        values = row.dropna()
        if not values.empty:
            return normalize_number(values.iloc[0])

    return None


def first_available(*values):
    for value in values:
        if value is not None:
            return value
    return None


def get_stock_data(symbol: str) -> FinancialData:
    yf_symbol = normalize_symbol(symbol)
    ticker = yf.Ticker(yf_symbol)

    info = ticker.info
    financials = ticker.financials
    balance_sheet = ticker.balance_sheet
    cashflow = ticker.cashflow

    if not info:
        raise ValueError("抓不到股票資料，請確認代號是否正確。")

    return FinancialData(
        symbol=yf_symbol,
        company_name=safe_info_get(info, "longName", "未知公司"),
        industry=safe_info_get(info, "industry", "未知產業"),
        sector=safe_info_get(info, "sector", "未知類別"),
        price=normalize_number(safe_info_get(info, "currentPrice")),
        net_income=latest_statement_value(financials, ["Net Income"]),
        total_assets=latest_statement_value(balance_sheet, ["Total Assets"]),
        total_equity=latest_statement_value(
            balance_sheet,
            ["Stockholders Equity", "Total Stockholder Equity", "Total Equity Gross Minority Interest"],
        ),
        total_debt=first_available(
            latest_statement_value(balance_sheet, ["Total Debt"]),
            normalize_number(safe_info_get(info, "totalDebt")),
        ),
        current_assets=latest_statement_value(balance_sheet, ["Current Assets", "Total Current Assets"]),
        current_liabilities=latest_statement_value(
            balance_sheet,
            ["Current Liabilities", "Total Current Liabilities"],
        ),
        revenue=latest_statement_value(financials, ["Total Revenue", "Revenue"]),
        gross_profit=latest_statement_value(financials, ["Gross Profit"]),
        operating_income=latest_statement_value(financials, ["Operating Income"]),
        operating_cashflow=first_available(
            latest_statement_value(cashflow, ["Operating Cash Flow", "Total Cash From Operating Activities"]),
            normalize_number(safe_info_get(info, "operatingCashflow")),
        ),
        free_cashflow=first_available(
            latest_statement_value(cashflow, ["Free Cash Flow"]),
            normalize_number(safe_info_get(info, "freeCashflow")),
        ),
        shares_outstanding=first_available(
            latest_statement_value(balance_sheet, ["Ordinary Shares Number", "Share Issued"]),
            normalize_number(safe_info_get(info, "sharesOutstanding")),
        ),
        pe=normalize_number(safe_info_get(info, "trailingPE")),
        pb=normalize_number(safe_info_get(info, "priceToBook")),
    )
