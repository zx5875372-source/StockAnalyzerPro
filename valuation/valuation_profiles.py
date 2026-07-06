from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ValuationProfile:
    name: str
    pe_min: float
    pe_max: float
    pb_min: float
    pb_max: float
    target_pe: float
    target_pb: float
    source: str = "industry_profile_v2"


VALUATION_PROFILES = {
    "半導體": ValuationProfile("半導體", pe_min=18, pe_max=30, pb_min=2.5, pb_max=5, target_pe=24, target_pb=3.75),
    "電子零組件": ValuationProfile("電子零組件", pe_min=12, pe_max=20, pb_min=1.5, pb_max=3, target_pe=16, target_pb=2.25),
    "通訊設備": ValuationProfile("通訊設備", pe_min=15, pe_max=25, pb_min=1.5, pb_max=3.5, target_pe=20, target_pb=2.5),
    "電腦及週邊": ValuationProfile("電腦及週邊", pe_min=15, pe_max=25, pb_min=1.5, pb_max=3.5, target_pe=20, target_pb=2.5),
    "金融": ValuationProfile("金融", pe_min=10, pe_max=15, pb_min=1, pb_max=2, target_pe=12.5, target_pb=1.5),
    "傳產": ValuationProfile("傳產", pe_min=8, pe_max=15, pb_min=1, pb_max=2, target_pe=11.5, target_pb=1.5),
}


INDUSTRY_TO_PROFILE = {
    "Technology": "科技",
    "Communication Equipment": "通訊設備",
    "Semiconductors": "半導體",
    "Electronic Components": "電子零組件",
    "Computer Hardware": "電腦及週邊",
    "Consumer Electronics": "電子零組件",
    "Industrials": "傳產",
    "Basic Materials": "傳產",
    "Financial Services": "金融",
    "Healthcare": "傳產",
    "Consumer Cyclical": "傳產",
    "Consumer Defensive": "傳產",
    "Utilities": "傳產",
    "Real Estate": "傳產",
    "Energy": "傳產",
    "科技": "半導體",
    "通訊設備": "通訊設備",
    "半導體": "半導體",
    "電子零組件": "電子零組件",
    "電腦及週邊設備": "電腦及週邊",
    "電腦及週邊": "電腦及週邊",
    "消費性電子": "電子零組件",
    "工業": "傳產",
    "原物料": "傳產",
    "金融": "金融",
    "醫療保健": "傳產",
    "非必需消費": "傳產",
    "民生消費": "傳產",
    "公用事業": "傳產",
    "房地產": "傳產",
    "能源": "傳產",
}


def get_valuation_profile(industry: str | None, sector: str | None = None) -> tuple[ValuationProfile, dict]:
    raw_industry = clean_label(industry)
    raw_sector = clean_label(sector)
    profile_name = profile_name_for(raw_industry) or profile_name_for(raw_sector) or "傳產"
    profile = VALUATION_PROFILES[profile_name]
    return profile, {
        "industry": raw_industry or "-",
        "sector": raw_sector or "-",
        "profile": profile.name,
        "source": profile.source,
        "fallback_used": profile_name == "傳產" and profile_name_for(raw_industry) is None and profile_name_for(raw_sector) is None,
    }


def profile_name_for(value: str | None) -> str | None:
    if not value:
        return None
    mapped_name = INDUSTRY_TO_PROFILE.get(value)
    if mapped_name in VALUATION_PROFILES:
        return mapped_name
    if mapped_name and mapped_name in INDUSTRY_TO_PROFILE:
        nested_name = INDUSTRY_TO_PROFILE[mapped_name]
        if nested_name in VALUATION_PROFILES:
            return nested_name
    if value in VALUATION_PROFILES:
        return value
    return None


def clean_label(value: str | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text in {"-", "未知產業", "未知類別", "None", "nan"}:
        return None
    return text
