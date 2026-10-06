from modules.report.constants import INDUSTRY_TRANSLATIONS


def fmt(value, suffix=""):
    if value is None:
        return "資料不足"
    if isinstance(value, (int, float)):
        return f"{value:.2f}{suffix}"
    return f"{value}{suffix}"


def metric(value):
    if value is None:
        return "資料不足"
    if isinstance(value, (int, float)):
        return f"{value:,.2f}"
    return str(value)


def format_percent(value, *, value_is_ratio: bool = True) -> str:
    if value is None:
        return "資料不足"
    if not isinstance(value, (int, float)):
        return str(value)
    percent_value = value * 100 if value_is_ratio else value
    return f"{percent_value:,.2f}%"


def format_ratio(value) -> str:
    return metric(value)


def format_currency(value) -> str:
    return metric(value)


def compact_metric(value):
    if value is None:
        return "資料不足"
    if isinstance(value, (int, float)):
        text = f"{value:.2f}"
        return text.rstrip("0").rstrip(".")
    return str(value)


def range_text(values) -> str:
    if not values or len(values) != 2:
        return "資料不足"
    return f"{compact_metric(values[0])}~{compact_metric(values[1])}"


def percent(value):
    if value is None:
        return "資料不足"
    return f"{round(value * 100, 2)}%"


def money(value):
    if value is None:
        return "資料不足"
    return format_currency(value)


def yes_no(value):
    if value is True:
        return "通過"
    if value is False:
        return "未通過"
    return "資料不足"


def yes_no_plain(value: bool) -> str:
    return "是" if value else "否"


def numbered_lines(items: list[str]) -> str:
    return "\n".join(f"{index}. {item}" for index, item in enumerate(items, start=1))


def translate_industry(value) -> str:
    if value in {None, ""}:
        return "資料不足"
    return INDUSTRY_TRANSLATIONS.get(str(value), str(value))
