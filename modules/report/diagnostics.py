from modules.report.constants import (
    ADVANCED_DIAGNOSTIC_MARKERS,
    CRITICAL_MISSING_FIELDS,
    DIAGNOSTIC_LABELS,
)


def data_completeness_summary(result: dict) -> dict:
    missing_fields = extract_still_missing_fields(result)
    if result.get("price") is None:
        missing_fields.append("current_price")

    unique_missing_fields = sorted(set(missing_fields))
    missing_text = "無" if not unique_missing_fields else ", ".join(unique_missing_fields)
    has_critical_missing = any(field in CRITICAL_MISSING_FIELDS for field in unique_missing_fields)

    if not unique_missing_fields:
        status = "完整"
    elif has_critical_missing:
        status = "資料不足"
    else:
        status = "部分缺漏"

    return {
        "status": status,
        "primary_source": primary_source(result),
        "supplement_source": supplement_source(result),
        "missing_text": missing_text,
    }


def extract_still_missing_fields(result: dict) -> list[str]:
    fields = []
    for item in result.get("diagnostics", []):
        if not item.startswith("still_missing_fields:"):
            continue
        value = item.split(":", 1)[1].strip()
        if value and value != "-":
            fields.extend([field.strip() for field in value.split(",") if field.strip()])
    if fields:
        return fields
    return list(result.get("missing_fields", []))


def primary_source(result: dict) -> str:
    provider_source = result.get("provider_source") or "未知"
    if "fallback" in provider_source:
        return "Yahoo Finance"
    if "Yahoo" in provider_source:
        return "Yahoo Finance"
    if "FinMind" in provider_source:
        return "FinMind"
    return provider_source


def supplement_source(result: dict) -> str:
    diagnostics = result.get("diagnostics", [])
    if primary_source(result) == "FinMind" and any(
        item.startswith("yahoo_enriched_fields:") and item.split(":", 1)[1].strip() != "-"
        for item in diagnostics
    ):
        return "Yahoo Finance"
    if result.get("provider_fallback_used"):
        return "FinMind fallback"
    return "無"


def split_diagnostics(diagnostics: list[str]) -> tuple[list[str], list[str]]:
    general = []
    advanced = []
    for item in diagnostics:
        if is_advanced_diagnostic(item):
            advanced.append(item)
        else:
            general.append(item)
    return general or ["無明顯缺漏"], advanced or ["無"]


def localize_diagnostic(item: str) -> str:
    if ":" not in item:
        return item
    key, value = item.split(":", 1)
    label = DIAGNOSTIC_LABELS.get(key.strip())
    if label is None:
        return item
    return f"{label}：{value.strip()}"


def diagnostic_lines(items: list[str]) -> str:
    return "\n".join([f"- {localize_diagnostic(item)}" for item in items])


def is_advanced_diagnostic(item: str) -> bool:
    return any(marker in item for marker in ADVANCED_DIAGNOSTIC_MARKERS)
