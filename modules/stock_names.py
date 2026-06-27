TAIWAN_STOCK_NAME_FALLBACKS = {
    "6285.TW": "啟碁",
    "2330.TW": "台積電",
    "2454.TW": "聯發科",
    "2327.TW": "國巨",
    "6271.TW": "同欣電",
    "3189.TW": "景碩",
    "3265.TWO": "台星科",
    "1605.TW": "華新",
    "6290.TWO": "良維",
    "2344.TW": "華邦電",
    "2408.TW": "南亞科",
    "6187.TW": "萬潤",
    "1735.TW": "日勝化",
    "9945.TW": "潤泰新",
}


def taiwan_stock_name(symbol: str) -> str | None:
    return TAIWAN_STOCK_NAME_FALLBACKS.get(normalize_symbol(symbol))


def normalize_symbol(symbol: str) -> str:
    text = str(symbol).strip().upper()
    if text.endswith(".TW") or text.endswith(".TWO"):
        return text
    if text.isdigit():
        return text + ".TW"
    return text
