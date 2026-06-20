from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import yfinance as yf

from backtest.integrity import calculate_credibility
from backtest.performance import PerformanceReport
from backtest.portfolio import Portfolio
from backtest.snapshot import SnapshotScoreStore
from backtest.strategy import BaseStrategy
from modules.downloader import normalize_symbol
from scan import load_sample_stocks


GENERATED_SNAPSHOT_PATH = Path("data/snapshots/generated_sap_scores.csv")
SAMPLE_SNAPSHOT_PATH = Path("data/snapshots/sample_sap_scores.csv")


@dataclass
class BacktestConfig:
    initial_cash: float = 1_000_000
    start_date: str = "2023-01-01"
    end_date: str = "2025-12-31"
    universe_path: Path = Path("tests/sample_data/sample_stocks.json")
    snapshot_path: Path | None = None
    min_sap_score: int = 80
    min_piotroski_score: int = 7
    min_data_quality_score: int = 80

    def resolved_snapshot_path(self) -> Path:
        if self.snapshot_path is not None:
            return Path(self.snapshot_path)
        if GENERATED_SNAPSHOT_PATH.exists():
            return GENERATED_SNAPSHOT_PATH
        return SAMPLE_SNAPSHOT_PATH


class YFinancePriceProvider:
    def load_price_history(self, symbols: list[str], start_date: str, end_date: str) -> tuple[dict[str, pd.Series], list[str]]:
        prices = {}
        diagnostics = []
        download_end_date = (pd.Timestamp(end_date) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")

        for symbol in symbols:
            yf_symbol = normalize_symbol(symbol)
            try:
                frame = yf.download(
                    yf_symbol,
                    start=start_date,
                    end=download_end_date,
                    progress=False,
                    auto_adjust=True,
                    threads=False,
                )
            except Exception as error:
                diagnostics.append(f"{yf_symbol}: price download failed - {error}")
                continue

            if frame.empty:
                diagnostics.append(f"{yf_symbol}: no historical price data")
                continue

            close = self._close_series(frame)
            if close is None or close.dropna().empty:
                diagnostics.append(f"{yf_symbol}: missing close price data")
                continue

            prices[yf_symbol] = close.dropna()

        return prices, diagnostics

    @staticmethod
    def _close_series(frame: pd.DataFrame):
        if "Close" in frame:
            close = frame["Close"]
            if isinstance(close, pd.DataFrame):
                return close.iloc[:, 0]
            return close
        if ("Close",) in frame:
            close = frame[("Close",)]
            if isinstance(close, pd.DataFrame):
                return close.iloc[:, 0]
            return close
        if isinstance(frame.columns, pd.MultiIndex):
            close_columns = [column for column in frame.columns if "Close" in column]
            if close_columns:
                close = frame[close_columns[0]]
                if isinstance(close, pd.DataFrame):
                    return close.iloc[:, 0]
                return close
        return None


class BacktestEngine:
    def __init__(
        self,
        strategy: BaseStrategy,
        portfolio: Portfolio,
        config: BacktestConfig | None = None,
        price_provider: YFinancePriceProvider | None = None,
    ):
        self.strategy = strategy
        self.portfolio = portfolio
        self.config = config or BacktestConfig()
        self.price_provider = price_provider or YFinancePriceProvider()
        self.universe = []
        self.snapshots = SnapshotScoreStore()
        self.price_history = {}
        self.diagnostics = []
        self.selected_symbols = []
        self.skipped_reasons = {}
        self.look_ahead_safe = False
        self.snapshot_source = self.config.resolved_snapshot_path()

    def load_data(self) -> None:
        raw_universe = load_sample_stocks(self.config.universe_path)
        self.universe = [
            {
                **stock,
                "symbol": normalize_symbol(stock["symbol"]),
            }
            for stock in raw_universe
        ]

        print("載入 historical SAP Score snapshot...")
        self.snapshot_source = self.config.resolved_snapshot_path()
        self.snapshots = SnapshotScoreStore.from_csv(self.snapshot_source)
        self.diagnostics.extend(self.snapshots.diagnostics)
        self.look_ahead_safe = self.snapshots.available()

        print("下載歷史價格...")
        symbols = [stock["symbol"] for stock in self.universe]
        self.price_history, price_diagnostics = self.price_provider.load_price_history(
            symbols,
            self.config.start_date,
            self.config.end_date,
        )
        self.diagnostics.extend(price_diagnostics)

    def run(self) -> dict:
        if not self.universe:
            self.load_data()

        rebalance_dates = self._rebalance_dates()
        data = {
            "snapshots": self.snapshots,
            "price_history": self.price_history,
        }

        self.portfolio.record_equity(
            pd.Timestamp(self.config.start_date),
            self._price_snapshot(pd.Timestamp(self.config.start_date)),
        )

        for date in rebalance_dates:
            price_snapshot = self._price_snapshot(date)
            selected_candidates = self.strategy.select_stocks(date, self.universe, data)
            self.skipped_reasons.update(getattr(self.strategy, "skipped_reasons", {}))
            selected = [symbol for symbol in selected_candidates if symbol in price_snapshot]
            missing_price_symbols = [
                symbol
                for symbol in selected_candidates
                if symbol not in price_snapshot
            ]
            for symbol in missing_price_symbols:
                self.skipped_reasons[symbol] = f"missing price on or before {date.date()}"
            for symbol in selected:
                self.skipped_reasons.pop(symbol, None)
            self.selected_symbols = selected

            if selected:
                target_weights = self.strategy.rebalance(date, self.portfolio, selected)
                self.portfolio.update_positions(date, target_weights, price_snapshot)
            else:
                self.portfolio.record_history(date, "no selected stocks")

            self.portfolio.record_equity(date, price_snapshot)

        metrics = PerformanceReport(self.portfolio.equity_curve).calculate()
        summary = self.summary()
        return {
            "config": summary,
            "strategy_name": self.strategy.name,
            "metrics": metrics,
            "equity_curve": self.portfolio.equity_curve,
            "history": self.portfolio.history,
            "selected_symbols": self.selected_symbols,
            "selected_stock_count": summary["selected_stock_count"],
            "skipped_stock_count": summary["skipped_stock_count"],
            "skipped_reasons": self.skipped_reasons,
            "snapshot_source": summary["snapshot_path"],
            "snapshot_warning_counts": summary["snapshot_warning_counts"],
            "snapshot_point_in_time": summary["snapshot_point_in_time"],
            "look_ahead_safe": summary["look_ahead_safe"],
            "credibility_grade": summary["credibility_grade"],
            "credibility_reason": summary["credibility_reason"],
            "credibility_notice": summary["credibility_notice"],
            "diagnostics": self.diagnostics,
        }

    def summary(self) -> dict:
        snapshot_warning_counts = self.snapshots.warning_counts()
        selected_stock_count = len(self.selected_symbols)
        skipped_stock_count = len(self.skipped_reasons)
        snapshot_point_in_time = snapshot_warning_counts.get("not_point_in_time", 0) == 0
        credibility = calculate_credibility(
            look_ahead_safe=self.look_ahead_safe,
            snapshot_warning_counts=snapshot_warning_counts,
            selected_stock_count=selected_stock_count,
            data_available=self.snapshots.available() and bool(self.price_history),
        )

        return {
            "initial_cash": self.config.initial_cash,
            "start_date": self.config.start_date,
            "end_date": self.config.end_date,
            "universe_path": str(self.config.universe_path),
            "snapshot_path": str(self.config.resolved_snapshot_path()),
            "min_sap_score": self.config.min_sap_score,
            "min_piotroski_score": self.config.min_piotroski_score,
            "min_data_quality_score": self.config.min_data_quality_score,
            "credibility_grade": credibility["credibility_grade"],
            "credibility_reason": credibility["credibility_reason"],
            "look_ahead_safe": self.look_ahead_safe,
            "snapshot_point_in_time": snapshot_point_in_time,
            "snapshot_warning_counts": snapshot_warning_counts,
            "selected_stock_count": selected_stock_count,
            "skipped_stock_count": skipped_stock_count,
            "credibility_notice": credibility["credibility_notice"],
        }

    def _rebalance_dates(self) -> list[pd.Timestamp]:
        dates = pd.date_range(
            start=self.config.start_date,
            end=self.config.end_date,
            freq="ME",
        )
        return list(dates)

    def _price_snapshot(self, date: pd.Timestamp) -> dict[str, float]:
        snapshot = {}
        for symbol, series in self.price_history.items():
            available = series.loc[series.index <= date]
            if available.empty:
                continue
            snapshot[symbol] = float(available.iloc[-1])
        return snapshot
