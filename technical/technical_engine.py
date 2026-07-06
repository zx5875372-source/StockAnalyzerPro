from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Callable

import pandas as pd
import yfinance as yf

from modules.downloader import normalize_symbol
from technical.indicators import macd as calculate_macd
from technical.indicators import moving_average, rsi as calculate_rsi
from technical.indicators import volume_ratio as calculate_volume_ratio


HistoryLoader = Callable[[str, str], pd.DataFrame]


@dataclass
class TechnicalResult:
    trend_score: int = 0
    technical_grade: str = "D"
    ma20: float | None = None
    ma60: float | None = None
    ma120: float | None = None
    ma240: float | None = None
    rsi14: float | None = None
    rsi_status: str = "資料不足"
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    macd_status: str = "資料不足"
    volume_ratio: float | None = None
    golden_cross: bool = False
    death_cross: bool = False
    diagnostics: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


class TechnicalAnalysis:
    def __init__(self, history_loader: HistoryLoader | None = None, period: str = "2y"):
        self.history_loader = history_loader or self._load_yahoo_history
        self.period = period

    def analyze(self, symbol: str) -> TechnicalResult:
        normalized_symbol = normalize_symbol(symbol)
        diagnostics = [
            "technical_source: Yahoo Finance",
            f"technical_period: {self.period}",
        ]
        try:
            history = self.history_loader(normalized_symbol, self.period)
        except Exception as error:
            diagnostics.extend(
                [
                    "technical_price_count: 0",
                    f"technical_missing_fields: history ({error})",
                ]
            )
            return TechnicalResult(diagnostics=diagnostics)

        if history is None or history.empty:
            diagnostics.extend(["technical_price_count: 0", "technical_missing_fields: history"])
            return TechnicalResult(diagnostics=diagnostics)

        close = self._column(history, "Close")
        volume = self._column(history, "Volume")
        price_count = len(close.dropna()) if close is not None else 0
        diagnostics.append(f"technical_price_count: {price_count}")

        missing_fields = []
        if close is None or price_count == 0:
            missing_fields.append("Close")
        if volume is None or len(volume.dropna()) == 0:
            missing_fields.append("Volume")

        if close is None or price_count == 0:
            diagnostics.append("technical_missing_fields: " + ", ".join(missing_fields))
            return TechnicalResult(diagnostics=diagnostics)

        ma20 = moving_average(close, 20)
        ma60 = moving_average(close, 60)
        ma120 = moving_average(close, 120)
        ma240 = moving_average(close, 240)
        rsi14 = calculate_rsi(close, 14)
        macd_values = calculate_macd(close)
        volume_ratio = calculate_volume_ratio(volume, 20) if volume is not None else None

        for field_name, value in {
            "ma20": ma20,
            "ma60": ma60,
            "ma120": ma120,
            "ma240": ma240,
            "rsi14": rsi14,
            "macd": macd_values["macd"],
            "macd_signal": macd_values["signal"],
            "macd_histogram": macd_values["histogram"],
            "volume_ratio": volume_ratio,
        }.items():
            if value is None:
                missing_fields.append(field_name)

        current_price = float(close.dropna().iloc[-1])
        golden_cross = self._golden_cross(macd_values)
        death_cross = self._death_cross(macd_values)
        rsi_status = self._rsi_status(rsi14)
        macd_status = self._macd_status(macd_values["macd"], macd_values["signal"])
        trend_score = self._trend_score(
            current_price=current_price,
            ma20=ma20,
            ma60=ma60,
            ma120=ma120,
            ma240=ma240,
            rsi14=rsi14,
            macd_value=macd_values["macd"],
            macd_signal=macd_values["signal"],
            volume_ratio=volume_ratio,
        )

        diagnostics.append("technical_missing_fields: " + (", ".join(sorted(set(missing_fields))) if missing_fields else "-"))

        return TechnicalResult(
            trend_score=trend_score,
            technical_grade=self._technical_grade(trend_score),
            ma20=ma20,
            ma60=ma60,
            ma120=ma120,
            ma240=ma240,
            rsi14=rsi14,
            rsi_status=rsi_status,
            macd=macd_values["macd"],
            macd_signal=macd_values["signal"],
            macd_histogram=macd_values["histogram"],
            macd_status=macd_status,
            volume_ratio=volume_ratio,
            golden_cross=golden_cross,
            death_cross=death_cross,
            diagnostics=diagnostics,
        )

    @staticmethod
    def _load_yahoo_history(symbol: str, period: str) -> pd.DataFrame:
        return yf.Ticker(symbol).history(period=period)

    @staticmethod
    def _column(history: pd.DataFrame, name: str) -> pd.Series | None:
        if name not in history.columns:
            return None
        return history[name]

    @staticmethod
    def _rsi_status(value: float | None) -> str:
        if value is None:
            return "資料不足"
        if value < 30:
            return "超賣"
        if value > 70:
            return "超買"
        return "正常"

    @staticmethod
    def _macd_status(macd_value: float | None, signal_value: float | None) -> str:
        if macd_value is None or signal_value is None:
            return "資料不足"
        if macd_value > signal_value:
            return "偏多"
        if macd_value < signal_value:
            return "偏空"
        return "中性"

    @staticmethod
    def _golden_cross(values: dict) -> bool:
        previous_macd = values.get("previous_macd")
        previous_signal = values.get("previous_signal")
        current_macd = values.get("macd")
        current_signal = values.get("signal")
        if None in {previous_macd, previous_signal, current_macd, current_signal}:
            return False
        return previous_macd <= previous_signal and current_macd > current_signal

    @staticmethod
    def _death_cross(values: dict) -> bool:
        previous_macd = values.get("previous_macd")
        previous_signal = values.get("previous_signal")
        current_macd = values.get("macd")
        current_signal = values.get("signal")
        if None in {previous_macd, previous_signal, current_macd, current_signal}:
            return False
        return previous_macd >= previous_signal and current_macd < current_signal

    @classmethod
    def _trend_score(
        cls,
        *,
        current_price: float,
        ma20: float | None,
        ma60: float | None,
        ma120: float | None,
        ma240: float | None,
        rsi14: float | None,
        macd_value: float | None,
        macd_signal: float | None,
        volume_ratio: float | None,
    ) -> int:
        score = 0

        ma_checks = [
            ma20 is not None and current_price > ma20,
            ma20 is not None and ma60 is not None and ma20 > ma60,
            ma60 is not None and ma120 is not None and ma60 > ma120,
            ma120 is not None and ma240 is not None and ma120 > ma240,
        ]
        score += sum(10 for passed in ma_checks if passed)

        if rsi14 is not None:
            if 30 <= rsi14 <= 70:
                score += 20
            elif rsi14 < 30:
                score += 10
            else:
                score += 5

        if macd_value is not None and macd_signal is not None:
            score += 25 if macd_value > macd_signal else 10

        if volume_ratio is not None:
            if volume_ratio >= 1:
                score += 15
            elif volume_ratio > 0:
                score += 8

        return min(score, 100)

    @staticmethod
    def _technical_grade(score: int) -> str:
        if score >= 90:
            return "S"
        if score >= 80:
            return "A"
        if score >= 70:
            return "B"
        if score >= 60:
            return "C"
        return "D"
