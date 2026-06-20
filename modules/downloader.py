import pandas as pd
import yfinance as yf

from models.financial_data import FinancialData, FinancialPeriod, safe_divide


FIELD_ALIASES = {
    "net_income": [
        "Net Income",
        "Net Income Common Stockholders",
        "Net Income From Continuing Operation Net Minority Interest",
        "Net Income From Continuing And Discontinued Operation",
    ],
    "total_assets": ["Total Assets"],
    "total_equity": [
        "Stockholders Equity",
        "Common Stock Equity",
        "Total Stockholder Equity",
        "Total Equity Gross Minority Interest",
    ],
    "total_debt": ["Total Debt"],
    "long_term_debt": [
        "Long Term Debt",
        "Long Term Debt And Capital Lease Obligation",
        "Non Current Debt",
        "Long Term Debt Non Current",
    ],
    "current_assets": ["Current Assets", "Total Current Assets"],
    "current_liabilities": ["Current Liabilities", "Total Current Liabilities"],
    "revenue": ["Total Revenue", "Operating Revenue", "Revenue"],
    "gross_profit": ["Gross Profit"],
    "operating_income": ["Operating Income", "Total Operating Income As Reported"],
    "operating_cashflow": [
        "Operating Cash Flow",
        "Cash Flow From Continuing Operating Activities",
        "Total Cash From Operating Activities",
    ],
    "free_cashflow": ["Free Cash Flow"],
    "shares_outstanding": ["Ordinary Shares Number", "Share Issued"],
}

FIELD_SOURCES = {
    "net_income": "financials",
    "revenue": "financials",
    "gross_profit": "financials",
    "operating_income": "financials",
    "total_assets": "balance_sheet",
    "total_equity": "balance_sheet",
    "total_debt": "balance_sheet",
    "long_term_debt": "balance_sheet",
    "current_assets": "balance_sheet",
    "current_liabilities": "balance_sheet",
    "shares_outstanding": "balance_sheet",
    "operating_cashflow": "cashflow",
    "free_cashflow": "cashflow",
}

INFO_FALLBACKS = {
    "total_debt": "totalDebt",
    "operating_cashflow": "operatingCashflow",
    "free_cashflow": "freeCashflow",
    "shares_outstanding": "sharesOutstanding",
}

VALUATION_INFO_FALLBACKS = {
    "eps": "trailingEps",
    "book_value_per_share": "bookValue",
}


def normalize_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()

    if symbol.endswith(".TW") or symbol.endswith(".TWO"):
        return symbol

    if symbol.isdigit():
        return symbol + ".TW"

    return symbol


def safe_info_get(info: dict, key: str, default=None):
    value = info.get(key, default)
    return value if value is not None else default


def normalize_number(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def first_available(*values):
    for value in values:
        if value is not None:
            return value
    return None


def normalize_label(value) -> str:
    return str(value).strip().lower()


def sorted_statement_columns(statement) -> list:
    if statement is None or statement.empty:
        return []

    def sort_key(column):
        parsed = pd.to_datetime(column, errors="coerce")
        if pd.isna(parsed):
            return pd.Timestamp.min
        return parsed

    return sorted(statement.columns, key=sort_key, reverse=True)


def period_label(statement, period_index: int) -> str | None:
    columns = sorted_statement_columns(statement)
    if len(columns) <= period_index:
        return None

    column = columns[period_index]
    parsed = pd.to_datetime(column, errors="coerce")
    if pd.isna(parsed):
        return str(column)
    return parsed.strftime("%Y-%m-%d")


def statement_value(statement, row_aliases: list[str], period_index: int):
    columns = sorted_statement_columns(statement)
    if len(columns) <= period_index:
        return None

    index_lookup = {normalize_label(index): index for index in statement.index}
    for row_alias in row_aliases:
        matched_index = index_lookup.get(normalize_label(row_alias))
        if matched_index is None:
            continue

        value = statement.loc[matched_index, columns[period_index]]
        if isinstance(value, pd.Series):
            value = value.iloc[0]
        return normalize_number(value)

    return None


def get_field_value(field_name: str, statements: dict, info: dict, period_index: int):
    source = FIELD_SOURCES[field_name]
    value = statement_value(statements[source], FIELD_ALIASES[field_name], period_index)

    if period_index == 0 and value is None and field_name in INFO_FALLBACKS:
        value = normalize_number(safe_info_get(info, INFO_FALLBACKS[field_name]))

    return value


def build_period(period_index: int, statements: dict, info: dict, missing_fields: list[str]) -> FinancialPeriod | None:
    labels = [
        period_label(statements["financials"], period_index),
        period_label(statements["balance_sheet"], period_index),
        period_label(statements["cashflow"], period_index),
    ]
    label = first_available(*labels)

    if label is None:
        return None

    values = {}
    for field_name in FIELD_ALIASES:
        value = get_field_value(field_name, statements, info, period_index)
        values[field_name] = value
        if value is None:
            period_name = "current" if period_index == 0 else "previous"
            missing_fields.append(f"{period_name}.{field_name}")

    values["eps"] = safe_divide(values["net_income"], values["shares_outstanding"], precision=4)
    values["book_value_per_share"] = safe_divide(
        values["total_equity"],
        values["shares_outstanding"],
        precision=4,
    )

    if period_index == 0:
        values["eps"] = first_available(
            values["eps"],
            normalize_number(safe_info_get(info, VALUATION_INFO_FALLBACKS["eps"])),
        )
        values["book_value_per_share"] = first_available(
            values["book_value_per_share"],
            normalize_number(safe_info_get(info, VALUATION_INFO_FALLBACKS["book_value_per_share"])),
        )

    for valuation_field in ["eps", "book_value_per_share"]:
        if values[valuation_field] is None:
            period_name = "current" if period_index == 0 else "previous"
            missing_fields.append(f"{period_name}.{valuation_field}")

    return FinancialPeriod(period=label, **values)


def build_diagnostics(current: FinancialPeriod | None, previous: FinancialPeriod | None, missing_fields: list[str]) -> list[str]:
    diagnostics = []

    if current is None or current.period is None:
        diagnostics.append("缺少最新年度財報資料")
    if previous is None or previous.period is None:
        diagnostics.append("缺少前一年度財報資料，暫時無法做年度比較")
    if missing_fields:
        diagnostics.append("缺少欄位：" + ", ".join(missing_fields))

    return diagnostics


def get_stock_data(symbol: str) -> FinancialData:
    yf_symbol = normalize_symbol(symbol)
    ticker = yf.Ticker(yf_symbol)

    info = ticker.info
    statements = {
        "financials": ticker.financials,
        "balance_sheet": ticker.balance_sheet,
        "cashflow": ticker.cashflow,
    }

    if not info:
        raise ValueError("抓不到股票資料，請確認代號是否正確。")

    missing_fields = []
    current = build_period(0, statements, info, missing_fields) or FinancialPeriod()
    previous = build_period(1, statements, info, missing_fields)
    diagnostics = build_diagnostics(current, previous, missing_fields)

    return FinancialData(
        symbol=yf_symbol,
        company_name=safe_info_get(info, "longName", "未知公司"),
        industry=safe_info_get(info, "industry", "未知產業"),
        sector=safe_info_get(info, "sector", "未知類別"),
        price=normalize_number(safe_info_get(info, "currentPrice")),
        pe=normalize_number(safe_info_get(info, "trailingPE")),
        pb=normalize_number(safe_info_get(info, "priceToBook")),
        current=current,
        previous=previous,
        missing_fields=missing_fields,
        diagnostics=diagnostics,
    )
