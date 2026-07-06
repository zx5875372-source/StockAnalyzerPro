from __future__ import annotations

import pandas as pd


def moving_average(values: pd.Series, window: int) -> float | None:
    series = clean_series(values)
    if len(series) < window:
        return None
    return round(float(series.tail(window).mean()), 2)


def rsi(values: pd.Series, period: int = 14) -> float | None:
    series = clean_series(values)
    if len(series) <= period:
        return None

    delta = series.diff().dropna()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    average_gain = gains.tail(period).mean()
    average_loss = losses.tail(period).mean()

    if average_loss == 0:
        return 100.0
    relative_strength = average_gain / average_loss
    return round(float(100 - (100 / (1 + relative_strength))), 2)


def macd(values: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    series = clean_series(values)
    if len(series) < slow + signal:
        return {
            "macd": None,
            "signal": None,
            "histogram": None,
            "previous_macd": None,
            "previous_signal": None,
        }

    fast_ema = series.ewm(span=fast, adjust=False).mean()
    slow_ema = series.ewm(span=slow, adjust=False).mean()
    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": round(float(macd_line.iloc[-1]), 4),
        "signal": round(float(signal_line.iloc[-1]), 4),
        "histogram": round(float(histogram.iloc[-1]), 4),
        "previous_macd": round(float(macd_line.iloc[-2]), 4),
        "previous_signal": round(float(signal_line.iloc[-2]), 4),
    }


def volume_ratio(volumes: pd.Series, window: int = 20) -> float | None:
    series = clean_series(volumes)
    if len(series) < window or series.iloc[-1] is None:
        return None
    average_volume = series.tail(window).mean()
    if average_volume <= 0:
        return None
    return round(float(series.iloc[-1] / average_volume), 2)


def clean_series(values: pd.Series) -> pd.Series:
    if values is None:
        return pd.Series(dtype="float64")
    return pd.to_numeric(values, errors="coerce").dropna()
