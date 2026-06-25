from __future__ import annotations

from datetime import date
from typing import Any

from models.financial_data import FinancialData, FinancialPeriod, safe_divide
from data_provider.interfaces import IDataProvider, PriceHistory, ProviderDiagnostic, ProviderError
from importers.finmind import FinMindClient
from modules.downloader import normalize_symbol


FIELD_ALIASES = {
    "revenue": [
        "revenue",
        "營業收入",
        "營業收入合計",
        "營收",
        "total revenue",
        "operating revenue",
    ],
    "net_income": [
        "net_income",
        "本期淨利",
        "本期淨利（淨損）",
        "本期淨利(淨損)",
        "稅後淨利",
        "net income",
    ],
    "total_assets": [
        "total_assets",
        "資產總額",
        "資產合計",
        "total assets",
    ],
    "total_liabilities": [
        "total_liabilities",
        "負債總額",
        "負債合計",
        "total liabilities",
    ],
    "total_equity": [
        "total_equity",
        "權益總額",
        "權益合計",
        "股東權益總額",
        "total equity",
    ],
    "cash_from_operations": [
        "cash_from_operations",
        "operating_cashflow",
        "營業活動之淨現金流入（流出）",
        "營業活動之淨現金流入(流出)",
        "營業活動現金流量",
        "cash flows from operating activities",
    ],
    "capital_expenditure": [
        "capital_expenditure",
        "資本支出",
        "購置不動產、廠房及設備",
        "取得不動產、廠房及設備",
        "capital expenditure",
    ],
    "gross_profit": [
        "gross_profit",
        "營業毛利",
        "營業毛利（毛損）",
        "營業毛利(毛損)",
        "gross profit",
    ],
    "shares_outstanding": [
        "shares_outstanding",
        "流通在外股數",
        "普通股股本",
        "股本",
        "shares outstanding",
    ],
    "eps": [
        "eps",
        "基本每股盈餘",
        "基本每股盈餘（元）",
        "basic eps",
    ],
    "book_value_per_share": [
        "book_value_per_share",
        "每股淨值",
        "book value per share",
    ],
}

PERIOD_FIELDS = [
    "revenue",
    "net_income",
    "total_assets",
    "total_equity",
    "total_debt",
    "gross_profit",
    "operating_cashflow",
    "free_cashflow",
    "shares_outstanding",
    "eps",
    "book_value_per_share",
]

ACCOUNT_KEYS = ["type", "name", "account", "item", "field", "label"]
VALUE_KEYS = ["value", "amount", "data", "number"]


class FinMindProvider(IDataProvider):
    name = "finmind"
    version = "financial-mapping-v1"

    def __init__(self, client: object | None = None):
        self.client = client or FinMindClient()
        self._diagnostics: list[ProviderDiagnostic] = []

    def get_financial_data(self, symbol: str, as_of: str | None = None) -> FinancialData:
        normalized_symbol = self.normalize_symbol(symbol)
        if not self.is_taiwan_symbol(normalized_symbol):
            message = f"{normalized_symbol}: FinMindProvider supports Taiwan stock symbols only; use Yahoo fallback"
            self._record("warning", message, normalized_symbol)
            raise ProviderError(message)

        stock_id = self.finmind_stock_id(normalized_symbol)
        rows = []
        rows.extend(self._client_rows("get_financial_statement", stock_id, as_of=as_of))
        rows.extend(self._client_rows("get_balance_sheet", stock_id, as_of=as_of))
        rows.extend(self._client_rows("get_cash_flow", stock_id, as_of=as_of))
        if not rows:
            message = f"{normalized_symbol}: no FinMind financial rows returned; use Yahoo fallback"
            self._record("warning", message, normalized_symbol)
            raise ProviderError(message)

        periods = self._build_periods(rows)
        if not periods:
            message = f"{normalized_symbol}: FinMind rows do not contain usable financial periods"
            self._record("warning", message, normalized_symbol)
            raise ProviderError(message)

        current_period_key, current_period = periods[0]
        previous_period = periods[1][1] if len(periods) > 1 else None
        missing_fields = self._missing_fields(current_period, prefix="current")
        if previous_period is None:
            missing_fields.append("previous")
        else:
            missing_fields.extend(self._missing_fields(previous_period, prefix="previous"))

        diagnostics = [
            f"FinMindProvider mapped {len(rows)} raw rows into FinancialData",
            f"current period: {current_period_key}",
        ]
        if previous_period is not None:
            diagnostics.append(f"previous period: {periods[1][0]}")
        if missing_fields:
            missing_text = ", ".join(missing_fields)
            diagnostics.append("missing fields: " + missing_text)
            self._record("warning", f"{normalized_symbol}: missing fields: {missing_text}", normalized_symbol)

        return FinancialData(
            symbol=normalized_symbol,
            company_name=self._company_name(stock_id),
            current=current_period,
            previous=previous_period,
            missing_fields=missing_fields,
            diagnostics=diagnostics,
        )

    def get_price_history(self, symbol: str, start: str | None = None, end: str | None = None) -> PriceHistory:
        normalized_symbol = self.normalize_symbol(symbol)
        message = f"{normalized_symbol}: FinMindProvider price history is not implemented yet; use Yahoo fallback"
        self._record("info", message, normalized_symbol)
        raise ProviderError(message)

    def get_universe(self, universe_id: str) -> list[str]:
        message = f"{universe_id}: FinMindProvider universe lookup is not implemented yet"
        self._record("info", message)
        raise ProviderError(message)

    def diagnostics(self) -> list[ProviderDiagnostic]:
        return list(self._diagnostics)

    def get_provider_diagnostics(self) -> list[ProviderDiagnostic]:
        return self.diagnostics()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        return normalize_symbol(symbol)

    @staticmethod
    def is_taiwan_symbol(symbol: str) -> bool:
        normalized = normalize_symbol(symbol)
        if normalized.endswith(".TW") or normalized.endswith(".TWO"):
            return normalized.split(".", 1)[0].isdigit()
        return False

    @staticmethod
    def finmind_stock_id(symbol: str) -> str:
        return normalize_symbol(symbol).split(".", 1)[0]

    def _record(self, severity: str, message: str, symbol: str | None = None) -> None:
        self._diagnostics.append(
            ProviderDiagnostic(
                provider=self.name,
                severity=severity,
                symbol=symbol,
                message=message,
            )
        )

    def _client_rows(self, method_name: str, stock_id: str, as_of: str | None = None) -> list[dict]:
        method = getattr(self.client, method_name, None)
        if method is None:
            return []
        try:
            response = method(stock_id, end_date=as_of)
        except TypeError:
            response = method(stock_id)
        return self._extract_rows(response)

    @staticmethod
    def _extract_rows(response: Any) -> list[dict]:
        if response is None:
            return []
        if isinstance(response, list):
            return [row for row in response if isinstance(row, dict)]
        data = getattr(response, "data", None)
        if isinstance(data, list):
            return [row for row in data if isinstance(row, dict)]
        if isinstance(response, dict):
            data = response.get("data")
            if isinstance(data, list):
                return [row for row in data if isinstance(row, dict)]
        return []

    def _build_periods(self, rows: list[dict]) -> list[tuple[str, FinancialPeriod]]:
        grouped: dict[str, dict[str, float]] = {}
        sort_keys: dict[str, date] = {}
        for row in rows:
            period_key, sort_key = self._period_key(row)
            if not period_key or sort_key is None:
                continue
            grouped.setdefault(period_key, {})
            sort_keys[period_key] = sort_key
            self._merge_row_values(grouped[period_key], row)

        periods = []
        for period_key, values in grouped.items():
            period = self._financial_period(period_key, values)
            periods.append((period_key, sort_keys[period_key], period))
        periods.sort(key=lambda item: item[1], reverse=True)
        return [(period_key, period) for period_key, _, period in periods]

    def _merge_row_values(self, values: dict[str, float], row: dict) -> None:
        for internal_field, aliases in FIELD_ALIASES.items():
            direct_value = self._value_from_alias(row, aliases)
            if direct_value is not None:
                values[internal_field] = direct_value

        account_name = self._account_name(row)
        if not account_name:
            return
        amount = self._row_amount(row)
        if amount is None:
            return
        normalized_account = self._normalize_label(account_name)
        for internal_field, aliases in FIELD_ALIASES.items():
            if normalized_account in {self._normalize_label(alias) for alias in aliases}:
                values[internal_field] = amount
                return

    def _financial_period(self, period_key: str, values: dict[str, float]) -> FinancialPeriod:
        total_assets = values.get("total_assets")
        total_liabilities = values.get("total_liabilities")
        total_equity = values.get("total_equity")
        if total_equity is None and total_assets is not None and total_liabilities is not None:
            total_equity = total_assets - total_liabilities

        operating_cashflow = values.get("cash_from_operations")
        capital_expenditure = values.get("capital_expenditure")
        free_cashflow = self._free_cashflow(operating_cashflow, capital_expenditure)

        shares_outstanding = values.get("shares_outstanding")
        eps = values.get("eps")
        if eps is None:
            eps = safe_divide(values.get("net_income"), shares_outstanding, precision=4)
        book_value_per_share = values.get("book_value_per_share")
        if book_value_per_share is None:
            book_value_per_share = safe_divide(total_equity, shares_outstanding, precision=4)

        return FinancialPeriod(
            period=period_key,
            net_income=values.get("net_income"),
            total_assets=total_assets,
            total_equity=total_equity,
            total_debt=total_liabilities,
            revenue=values.get("revenue"),
            gross_profit=values.get("gross_profit"),
            operating_cashflow=operating_cashflow,
            free_cashflow=free_cashflow,
            shares_outstanding=shares_outstanding,
            eps=eps,
            book_value_per_share=book_value_per_share,
        )

    def _company_name(self, stock_id: str) -> str | None:
        method = getattr(self.client, "get_company_info", None)
        if method is None:
            return None
        try:
            info = method(stock_id)
        except Exception:
            return None
        if isinstance(info, dict):
            return info.get("company_name") or info.get("name") or info.get("shortName") or info.get("longName")
        return None

    @classmethod
    def _missing_fields(cls, period: FinancialPeriod, prefix: str) -> list[str]:
        missing = []
        for field_name in PERIOD_FIELDS:
            if getattr(period, field_name, None) is None:
                missing.append(f"{prefix}.{field_name}")
        return missing

    @classmethod
    def _value_from_alias(cls, row: dict, aliases: list[str]) -> float | None:
        alias_lookup = {cls._normalize_label(alias) for alias in aliases}
        for key, value in row.items():
            if cls._normalize_label(str(key)) in alias_lookup:
                return cls._to_float(value)
        return None

    @classmethod
    def _account_name(cls, row: dict) -> str | None:
        for key in ACCOUNT_KEYS:
            value = row.get(key)
            if value not in (None, ""):
                return str(value)
        return None

    @classmethod
    def _row_amount(cls, row: dict) -> float | None:
        for key in VALUE_KEYS:
            value = cls._to_float(row.get(key))
            if value is not None:
                return value
        return None

    @staticmethod
    def _normalize_label(value: str) -> str:
        return value.strip().lower().replace(" ", "").replace("_", "")

    @staticmethod
    def _to_float(value) -> float | None:
        if value in (None, ""):
            return None
        try:
            return float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _period_key(cls, row: dict) -> tuple[str | None, date | None]:
        statement_date = row.get("statement_date") or row.get("date")
        if statement_date:
            text = str(statement_date)
            try:
                return text, date.fromisoformat(text[:10])
            except ValueError:
                return text, None

        fiscal_year = cls._year(row.get("fiscal_year") or row.get("year"))
        fiscal_quarter = cls._quarter(row.get("fiscal_quarter") or row.get("quarter"))
        if fiscal_year is None or fiscal_quarter is None:
            return None, None
        month, day = {
            1: (3, 31),
            2: (6, 30),
            3: (9, 30),
            4: (12, 31),
        }[fiscal_quarter]
        period_date = date(fiscal_year, month, day)
        return period_date.isoformat(), period_date

    @staticmethod
    def _to_int(value) -> int | None:
        if value in (None, ""):
            return None
        try:
            return int(str(value).replace("Q", "").replace("q", "").strip())
        except (TypeError, ValueError):
            return None

    @classmethod
    def _year(cls, value) -> int | None:
        parsed = cls._to_int(value)
        if parsed is None:
            return None
        if parsed < 1911:
            return parsed + 1911
        return parsed

    @classmethod
    def _quarter(cls, value) -> int | None:
        parsed = cls._to_int(value)
        if parsed in {1, 2, 3, 4}:
            return parsed
        return None

    @staticmethod
    def _free_cashflow(operating_cashflow: float | None, capital_expenditure: float | None) -> float | None:
        if operating_cashflow is None or capital_expenditure is None:
            return None
        if capital_expenditure < 0:
            return operating_cashflow + capital_expenditure
        return operating_cashflow - capital_expenditure
