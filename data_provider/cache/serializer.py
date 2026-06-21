from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pandas as pd

from data_provider.interfaces import PriceHistory
from models.financial_data import FinancialData


SCHEMA_VERSION = 1


class CacheSerializationError(ValueError):
    pass


def serialize_payload(value: Any) -> dict:
    if isinstance(value, FinancialData):
        return {
            "type": "FinancialData",
            "schema_version": SCHEMA_VERSION,
            "payload": asdict(value),
        }

    if isinstance(value, PriceHistory):
        return {
            "type": "PriceHistory",
            "schema_version": SCHEMA_VERSION,
            "payload": {
                "symbol": value.symbol,
                "start": value.start,
                "end": value.end,
                "data": _serialize_price_frame(value.data),
            },
        }

    if isinstance(value, pd.DataFrame):
        raise CacheSerializationError("DataFrame payloads are not supported directly")

    if _is_json_value(value):
        return {
            "type": "JSON",
            "schema_version": SCHEMA_VERSION,
            "payload": value,
        }

    raise CacheSerializationError(f"Unsupported cache payload type: {type(value).__name__}")


def _serialize_price_frame(frame: pd.DataFrame) -> dict:
    normalized = frame.copy()
    normalized.index = normalized.index.map(str)
    return {
        "index": list(normalized.index),
        "columns": [str(column) for column in normalized.columns],
        "dtypes": {str(column): str(dtype) for column, dtype in normalized.dtypes.items()},
        "data": _json_clean(normalized.where(pd.notna(normalized), None).values.tolist()),
    }


def _is_json_value(value) -> bool:
    if value is None or isinstance(value, (str, int, float, bool)):
        return True
    if isinstance(value, list):
        return all(_is_json_value(item) for item in value)
    if isinstance(value, dict):
        return all(isinstance(key, str) and _is_json_value(item) for key, item in value.items())
    return False


def _json_clean(value):
    if isinstance(value, float) and pd.isna(value):
        return None
    if isinstance(value, list):
        return [_json_clean(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_clean(item) for key, item in value.items()}
    return value
