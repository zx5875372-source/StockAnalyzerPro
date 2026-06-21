from __future__ import annotations

import pandas as pd

from data_provider.cache.serializer import SCHEMA_VERSION, CacheSerializationError
from data_provider.interfaces import PriceHistory
from models.financial_data import FinancialData, FinancialPeriod


def deserialize_payload(envelope: dict):
    if not isinstance(envelope, dict):
        raise CacheSerializationError("Cache payload envelope must be a dict")

    payload_type = envelope.get("type")
    schema_version = envelope.get("schema_version")
    payload = envelope.get("payload")

    if schema_version != SCHEMA_VERSION:
        raise CacheSerializationError(f"Unsupported cache payload schema version: {schema_version}")

    if payload_type == "FinancialData":
        return _deserialize_financial_data(payload)
    if payload_type == "PriceHistory":
        return _deserialize_price_history(payload)
    if payload_type == "JSON":
        return payload

    raise CacheSerializationError(f"Unsupported cache payload type: {payload_type}")


def _deserialize_financial_data(payload: dict) -> FinancialData:
    current_payload = payload.get("current") or {}
    previous_payload = payload.get("previous")
    return FinancialData(
        symbol=payload["symbol"],
        company_name=payload.get("company_name"),
        industry=payload.get("industry"),
        sector=payload.get("sector"),
        price=payload.get("price"),
        pe=payload.get("pe"),
        pb=payload.get("pb"),
        current=FinancialPeriod(**current_payload),
        previous=FinancialPeriod(**previous_payload) if previous_payload else None,
        missing_fields=list(payload.get("missing_fields") or []),
        diagnostics=list(payload.get("diagnostics") or []),
    )


def _deserialize_price_history(payload: dict) -> PriceHistory:
    frame_payload = payload["data"]
    frame = pd.DataFrame(
        data=frame_payload["data"],
        index=frame_payload["index"],
        columns=frame_payload["columns"],
    )
    for column, dtype in frame_payload.get("dtypes", {}).items():
        if column not in frame.columns:
            continue
        try:
            frame[column] = frame[column].astype(dtype)
        except (TypeError, ValueError):
            continue
    parsed_index = pd.to_datetime(list(frame.index), errors="coerce")
    if not parsed_index.isna().any():
        frame.index = parsed_index
    return PriceHistory(
        symbol=payload["symbol"],
        data=frame,
        start=payload.get("start"),
        end=payload.get("end"),
    )
