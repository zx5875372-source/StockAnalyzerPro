from __future__ import annotations

from dataclasses import dataclass, field
import json
from json import JSONDecodeError
from urllib import parse, request
from urllib.error import HTTPError, URLError

from importers.finmind.config import FinMindConfig
from importers.finmind.exceptions import (
    FinMindAPIError,
    FinMindAuthenticationError,
    FinMindRateLimitError,
)
from importers.finmind.models import FinMindResponse


@dataclass
class FinMindSession:
    headers: dict[str, str] = field(default_factory=dict)

    def get(self, url: str, params: dict, timeout: int):
        full_url = f"{url}?{parse.urlencode(params)}"
        request_obj = request.Request(full_url, headers=self.headers, method="GET")
        try:
            with request.urlopen(request_obj, timeout=timeout) as response:
                text = response.read().decode("utf-8")
                return FinMindHTTPResponse(
                    status_code=response.status,
                    payload=_decode_payload(text),
                    text=text,
                )
        except HTTPError as error:
            text = error.read().decode("utf-8")
            return FinMindHTTPResponse(
                status_code=error.code,
                payload=_decode_payload(text),
                text=text,
            )


@dataclass
class FinMindHTTPResponse:
    status_code: int
    payload: dict
    text: str = ""


def _decode_payload(text: str) -> dict:
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


class FinMindClient:
    def __init__(
        self,
        config: FinMindConfig | None = None,
        session: FinMindSession | None = None,
    ):
        self.config = config or FinMindConfig()
        self.base_url = self.config.base_url
        self.token = self.config.token
        self.timeout = self.config.timeout
        self.max_retry = self.config.max_retry
        self.session = session or self._create_session()

    def _create_session(self) -> FinMindSession:
        session = FinMindSession()
        if self.token:
            session.headers["Authorization"] = f"Bearer {self.token}"
        return session

    def request(self, dataset: str, **params) -> FinMindResponse:
        stock_id = params.pop("stock_id", None) or params.pop("data_id", None)
        if not stock_id:
            raise FinMindAPIError("FinMind request requires stock_id or data_id")
        return self._request(dataset=dataset, stock_id=stock_id, **params)

    def get_financial_statement(
        self,
        stock_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinMindResponse:
        return self._request(
            dataset="TaiwanStockFinancialStatements",
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_balance_sheet(
        self,
        stock_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinMindResponse:
        return self._request(
            dataset="TaiwanStockBalanceSheet",
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_cash_flow(
        self,
        stock_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinMindResponse:
        return self._request(
            dataset="TaiwanStockCashFlowsStatement",
            stock_id=stock_id,
            start_date=start_date,
            end_date=end_date,
        )

    def get_financial_statements(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinMindResponse:
        return self.get_financial_statement(symbol, start_date=start_date, end_date=end_date)

    def get_cashflow_statement(
        self,
        symbol: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinMindResponse:
        return self.get_cash_flow(symbol, start_date=start_date, end_date=end_date)

    def _request(
        self,
        dataset: str,
        stock_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> FinMindResponse:
        params = {
            "dataset": dataset,
            "data_id": stock_id,
        }
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if self.token:
            params["token"] = self.token

        attempts = self.max_retry + 1
        last_error = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(
                    self.base_url,
                    params=params,
                    timeout=self.timeout,
                )
                return self._handle_response(
                    response,
                    dataset=dataset,
                    attempt=attempt,
                    attempts=attempts,
                )
            except FinMindAuthenticationError:
                raise
            except FinMindRateLimitError as error:
                last_error = error
                if attempt >= attempts:
                    raise
            except (FinMindAPIError, URLError, TimeoutError, OSError) as error:
                last_error = error
                if attempt >= attempts:
                    if isinstance(error, FinMindAPIError):
                        raise
                    raise FinMindAPIError(f"FinMind request failed for {dataset}: {error}") from error

        raise FinMindAPIError(f"FinMind request failed for {dataset}: {last_error}")

    def _handle_response(
        self,
        response,
        dataset: str,
        attempt: int,
        attempts: int,
    ) -> FinMindResponse:
        status_code = response.status_code
        payload = getattr(response, "payload", None) or {}
        message = str(payload.get("msg") or payload.get("message") or "")

        if status_code in {401, 403}:
            raise FinMindAuthenticationError(f"FinMind authentication failed for {dataset}: {message or status_code}")
        if status_code == 429:
            raise FinMindRateLimitError(
                f"FinMind rate limit for {dataset} on attempt {attempt}/{attempts}: {message}".strip()
            )
        if status_code >= 500:
            raise FinMindAPIError(f"FinMind server error for {dataset}: HTTP {status_code} {message}".strip())
        if status_code >= 400:
            raise FinMindAPIError(f"FinMind API error for {dataset}: HTTP {status_code} {message}".strip())

        payload_status = payload.get("status", status_code)
        if isinstance(payload_status, str) and payload_status.isdigit():
            payload_status = int(payload_status)
        if isinstance(payload_status, int) and payload_status >= 400:
            if payload_status in {401, 403}:
                raise FinMindAuthenticationError(f"FinMind authentication failed for {dataset}: {message}")
            if payload_status == 429:
                raise FinMindRateLimitError(f"FinMind rate limit for {dataset} on attempt {attempt}/{attempts}")
            raise FinMindAPIError(f"FinMind API error for {dataset}: {message or payload_status}")

        return FinMindResponse(
            status=status_code if isinstance(payload_status, str) else int(payload_status),
            message=message,
            data=list(payload.get("data") or []),
        )
