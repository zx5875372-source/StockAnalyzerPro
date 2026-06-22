from __future__ import annotations

from dataclasses import dataclass, field

from importers.finmind.config import FinMindConfig


@dataclass
class FinMindSession:
    headers: dict[str, str] = field(default_factory=dict)


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

    def request(self, dataset: str, **params):
        raise NotImplementedError("FinMindClient request methods are not implemented in this sprint")

    def get_financial_statements(self, symbol: str, start_date: str, end_date: str):
        raise NotImplementedError("FinMindClient request methods are not implemented in this sprint")

    def get_balance_sheet(self, symbol: str, start_date: str, end_date: str):
        raise NotImplementedError("FinMindClient request methods are not implemented in this sprint")

    def get_cashflow_statement(self, symbol: str, start_date: str, end_date: str):
        raise NotImplementedError("FinMindClient request methods are not implemented in this sprint")
