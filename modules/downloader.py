import yfinance as yf


def normalize_symbol(symbol: str) -> str:
    symbol = symbol.strip()

    if symbol.endswith(".TW") or symbol.endswith(".TWO"):
        return symbol

    if symbol.isdigit():
        return symbol + ".TW"

    return symbol


def get_stock_data(symbol: str) -> dict:
    yf_symbol = normalize_symbol(symbol)
    ticker = yf.Ticker(yf_symbol)

    info = ticker.info
    financials = ticker.financials
    balance_sheet = ticker.balance_sheet
    cashflow = ticker.cashflow

    if not info:
        raise ValueError("抓不到股票資料，請確認代號是否正確。")

    return {
        "symbol": yf_symbol,
        "info": info,
        "financials": financials,
        "balance_sheet": balance_sheet,
        "cashflow": cashflow,
    }
