MIN_SELECTED_STOCK_COUNT = 2
NOT_POINT_IN_TIME_WARNING = "not_point_in_time"
LOW_CREDIBILITY_NOTICE = "此結果僅供系統測試，不可作為投資策略績效依據。"


def calculate_credibility(
    *,
    look_ahead_safe: bool,
    snapshot_warning_counts: dict[str, int],
    selected_stock_count: int,
    data_available: bool = True,
) -> dict:
    if not data_available:
        return {
            "credibility_grade": "D",
            "credibility_reason": "資料不足，無法建立可信回測結果。",
            "credibility_notice": LOW_CREDIBILITY_NOTICE,
        }

    if selected_stock_count < MIN_SELECTED_STOCK_COUNT:
        return {
            "credibility_grade": "D",
            "credibility_reason": f"入選股票數 {selected_stock_count} 低於最低門檻 {MIN_SELECTED_STOCK_COUNT}。",
            "credibility_notice": LOW_CREDIBILITY_NOTICE,
        }

    if not look_ahead_safe:
        return {
            "credibility_grade": "C",
            "credibility_reason": "回測資料流程不是 look-ahead-safe。",
            "credibility_notice": LOW_CREDIBILITY_NOTICE,
        }

    if snapshot_warning_counts.get(NOT_POINT_IN_TIME_WARNING, 0) > 0:
        return {
            "credibility_grade": "C",
            "credibility_reason": "snapshot 含 not_point_in_time warning，仍屬 proxy 資料。",
            "credibility_notice": LOW_CREDIBILITY_NOTICE,
        }

    if snapshot_warning_counts:
        return {
            "credibility_grade": "B",
            "credibility_reason": "流程為 look-ahead-safe，但部分 snapshot 有 warning。",
            "credibility_notice": "",
        }

    return {
        "credibility_grade": "A",
        "credibility_reason": "流程為 look-ahead-safe，且 snapshot 無 warning。",
        "credibility_notice": "",
    }
