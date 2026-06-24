import os
import json
from pathlib import Path
import subprocess
import sys

from modules.downloader import get_stock_data
from modules.analyzer import analyze_stock
from modules.report import generate_markdown_report
from scan import OUTPUT_PATH, SUMMARY_PATH, TOP10_PATH, WATCHLIST_PATH, WATCHLIST_REPORT_PATH, run_scan


COMMON_STOCKS = [
    ("台積電", "2330"),
    ("聯發科", "2454"),
    ("國巨", "2327"),
    ("南亞科", "2408"),
    ("同欣電", "6290"),
    ("萬潤", "6187"),
]
RANK_LABELS = ["第1名", "第2名", "第3名"]


def wait_for_main_menu() -> None:
    input("按 Enter 返回主選單...")


def success_message(text: str) -> str:
    message = f"✅ {text}"
    encoding = getattr(sys.stdout, "encoding", None)
    if not encoding:
        return message
    try:
        message.encode(encoding)
    except UnicodeEncodeError:
        return text
    return message


def open_file(path: str | Path) -> bool:
    file_path = Path(path)
    if not file_path.exists():
        print(f"找不到檔案：{file_path}")
        return False

    resolved = str(file_path.resolve())
    if hasattr(os, "startfile"):
        os.startfile(resolved)  # type: ignore[attr-defined]
    else:
        subprocess.run(["cmd", "/c", "start", "", resolved], check=False)
    print(f"已開啟：{file_path}")
    return True


def load_watchlist_items(path: Path = WATCHLIST_PATH) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        payload = json.load(file)
    if not isinstance(payload, list):
        raise ValueError("watchlist.json 格式錯誤，必須是陣列。")
    return payload


def save_watchlist_items(items: list, path: Path = WATCHLIST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def item_to_symbol(item) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return str(item.get("symbol", ""))
    return ""


def normalize_watchlist_symbol(symbol: str) -> str:
    value = symbol.strip().upper()
    if value.isdigit():
        return f"{value}.TW"
    return value


def watchlist_compare_key(symbol: str) -> str:
    value = symbol.strip().upper()
    if "." in value:
        return value.split(".", 1)[0]
    return value


def add_watchlist_symbol(symbol: str, path: Path = WATCHLIST_PATH) -> tuple[bool, int, str]:
    normalized_symbol = normalize_watchlist_symbol(symbol)
    if not normalized_symbol:
        raise ValueError("股票代號不可空白。")

    items = load_watchlist_items(path)
    new_key = watchlist_compare_key(normalized_symbol)
    existing_keys = {watchlist_compare_key(item_to_symbol(item)) for item in items}
    if new_key in existing_keys:
        return False, len(items), normalized_symbol

    items.append(normalized_symbol)
    save_watchlist_items(items, path)
    return True, len(items), normalized_symbol


def remove_watchlist_index(index: int, path: Path = WATCHLIST_PATH) -> str:
    items = load_watchlist_items(path)
    if index < 1 or index > len(items):
        raise IndexError("選項超出範圍。")
    removed = items.pop(index - 1)
    save_watchlist_items(items, path)
    return item_to_symbol(removed)


def watchlist_symbols(path: Path = WATCHLIST_PATH) -> list[str]:
    return [item_to_symbol(item) for item in load_watchlist_items(path)]


def print_section(title: str) -> None:
    print("==============================")
    print(title)
    print("")


def analyze_single_stock() -> None:
    while True:
        print_section("分析單一股票")
        print("1. 常用股票")
        print("2. 輸入其他股票")
        print("0. 返回")
        print("==============================")
        choice = input("請選擇功能：").strip()

        if choice == "1":
            stock = select_common_stock()
        elif choice == "2":
            stock = prompt_custom_stock()
        elif choice == "0":
            return
        else:
            print("請輸入 0-2。\n")
            continue

        if stock is None:
            continue

        symbol, name = stock
        result = analyze_symbol(symbol, name)
        if result is None:
            wait_for_main_menu()
            return

        action = show_single_stock_result(*result)
        if action == "another":
            continue
        return


def select_common_stock() -> tuple[str, str] | None:
    while True:
        print("")
        print("常用股票")
        print("==============================")
        for index, (name, symbol) in enumerate(COMMON_STOCKS, start=1):
            print(f"{index}. {name}（{symbol}）")
        print("7. 其他股票")
        print("")
        print("0. 返回")
        print("==============================")
        choice = input("請選擇股票：").strip()

        if choice == "0":
            return None
        if choice == "7":
            return prompt_custom_stock()
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(COMMON_STOCKS):
                name, symbol = COMMON_STOCKS[index - 1]
                return symbol, name
        print("請輸入 0-7。\n")


def prompt_custom_stock() -> tuple[str, str] | None:
    symbol = input("請輸入股票代號（輸入 0 返回）：").strip()
    if symbol == "0":
        return None
    if not symbol:
        print("股票代號不可空白。\n")
        return None
    return symbol, ""


def analyze_symbol(symbol: str, name: str = "") -> tuple[dict, Path, str, str] | None:
    try:
        print("")
        print("正在下載資料...")
        data = get_stock_data(symbol)
        print("正在分析...")
        result = analyze_stock(data)
        print("正在產生報告...")
        report_path = Path(generate_markdown_report(result))
        return result, report_path, symbol, name
    except Exception as error:
        print(f"分析失敗：{error}\n")
        return None


def show_single_stock_result(result: dict, report_path: Path, requested_symbol: str, name: str) -> str:
    display_symbol = requested_symbol.strip().upper().replace(".TW", "")
    display_name = name or result.get("name") or ""

    while True:
        print("====================================")
        print("")
        print(f"股票：{display_symbol} {display_name}".rstrip())
        print("")
        print(f"SAP 評分：{result['sap_score']} 分")
        print(f"投資等級：{result['grade']}")
        print("")
        print("==========================")
        print("1. 開啟分析報告")
        print("2. 加入自選股")
        print("3. 分析另一檔股票")
        print("0. 返回主選單")
        print("==========================")
        choice = input("請選擇功能：").strip()

        if choice == "1":
            open_file(report_path)
        elif choice == "2":
            add_symbol_to_watchlist_flow(requested_symbol)
        elif choice == "3":
            return "another"
        elif choice == "0":
            return "menu"
        else:
            print("請輸入 0-3。\n")


def add_symbol_to_watchlist_flow(symbol: str) -> None:
    try:
        added, count, _ = add_watchlist_symbol(symbol)
    except ValueError as error:
        print(str(error))
        return

    if added:
        print("")
        print(success_message("已加入自選股"))
        print("")
        print(f"目前共有 {count} 檔股票")
    else:
        print("此股票已存在於自選股。")


def run_stock_scan(mode: str, title: str) -> None:
    rows = run_scan(mode)
    show_scan_result(title, rows, mode)


def show_scan_result(title: str, rows: list[dict], mode: str) -> None:
    success_rows = [row for row in rows if row["status"] == "success"]
    failed_count = len(rows) - len(success_rows)
    full_report = WATCHLIST_REPORT_PATH if mode == "watchlist" else SUMMARY_PATH

    while True:
        print("====================================")
        print("")
        print(f"{title}完成")
        print("")
        print(f"成功：{len(success_rows)} 檔")
        print(f"失敗：{failed_count} 檔")
        print("")
        print("本次前三名：")
        print("")
        for index, row in enumerate(success_rows[:3]):
            rank_label = RANK_LABELS[index]
            print(f"{rank_label} {row['symbol']}　SAP {row['sap_score']} 分")
        if not success_rows:
            print("無成功分析資料")
        print("")
        print("==========================")
        print("1. 查看完整報告")
        print("2. 查看排行榜")
        print("3. 開啟 CSV")
        print("0. 返回主選單")
        print("==========================")
        choice = input("請選擇功能：").strip()

        if choice == "1":
            open_file(full_report)
        elif choice == "2":
            open_file(TOP10_PATH)
        elif choice == "3":
            open_file(OUTPUT_PATH)
        elif choice == "0":
            return
        else:
            print("請輸入 0-3。\n")


def run_cli(script_name: str, args: list[str] | None = None, report_to_open: Path | None = None) -> None:
    command = [sys.executable, script_name]
    if args:
        command.extend(args)
    print("")
    print(f"正在執行：{' '.join(command)}")
    print("------------------------------------")
    result = subprocess.run(command, check=False)
    if result.returncode == 0:
        print("完成")
        if report_to_open:
            ask_open_report(report_to_open)
    else:
        print(f"失敗（代碼：{result.returncode}）")
    print("")
    wait_for_main_menu()


def ask_open_report(path: Path) -> None:
    print("")
    print("==========================")
    print("1. 開啟報告")
    print("0. 不開啟")
    print("==========================")
    choice = input("請選擇功能：").strip()
    if choice == "1":
        open_file(path)


def prompt_optional(label: str, default: str | None = None) -> str | None:
    suffix = f"（預設 {default}）" if default else "（可空白）"
    value = input(f"{label}{suffix}：").strip()
    if value:
        return value
    return default


def run_finmind_import() -> None:
    print("\n[4] 更新 FinMind 財報")
    stock = select_stock_for_tool()
    if stock is None:
        return

    symbol, _ = stock
    start_date = prompt_optional("開始日期 YYYY-MM-DD")
    end_date = prompt_optional("結束日期 YYYY-MM-DD")
    db_path = prompt_optional("資料庫路徑", "historical_snapshots.db")
    token = prompt_optional("FinMind 權杖")

    args = ["--symbol", symbol]
    if start_date:
        args.extend(["--start", start_date])
    if end_date:
        args.extend(["--end", end_date])
    if db_path:
        args.extend(["--db", db_path])
    if token:
        args.extend(["--token", token])

    run_cli("finmind_import.py", args, report_to_open=Path("reports/finmind_import_summary.md"))


def select_stock_for_tool() -> tuple[str, str] | None:
    print("==============================")
    print("1. 常用股票")
    print("2. 輸入其他股票")
    print("0. 返回")
    print("==============================")
    choice = input("請選擇功能：").strip()
    if choice == "1":
        return select_common_stock()
    if choice == "2":
        return prompt_custom_stock()
    return None


def run_historical_sap_generator() -> None:
    print("\n[5] 建立歷史 SAP 評分")
    print("==============================")
    print("1. 建立全部")
    print("2. 依股票篩選")
    print("3. 進階篩選")
    print("0. 返回")
    print("==============================")
    choice = input("請選擇功能：").strip()
    if choice == "0":
        return

    db_path = prompt_optional("資料庫路徑", "historical_snapshots.db")
    args = []
    if db_path:
        args.extend(["--db", db_path])

    if choice == "2":
        stock = select_stock_for_tool()
        if stock is None:
            return
        args.extend(["--symbol", stock[0]])
    elif choice == "3":
        symbol = prompt_optional("股票代號")
        year = prompt_optional("會計年度")
        quarter = prompt_optional("會計季度 1-4")
        if symbol:
            args.extend(["--symbol", symbol])
        if year:
            args.extend(["--year", year])
        if quarter:
            args.extend(["--quarter", quarter])
    elif choice != "1":
        print("請輸入 0-3。\n")
        wait_for_main_menu()
        return

    run_cli("historical_generate_sap.py", args, report_to_open=Path("reports/historical_generator_summary.md"))


def manage_watchlist() -> None:
    while True:
        print("=========================")
        print("自選股管理")
        print("")
        print("1. 查看自選股")
        print("2. 新增股票")
        print("3. 刪除股票")
        print("4. 分析全部自選股")
        print("")
        print("0. 返回")
        print("=========================")
        choice = input("請選擇功能：").strip()

        if choice == "1":
            show_watchlist()
        elif choice == "2":
            prompt_add_watchlist_symbol()
        elif choice == "3":
            prompt_remove_watchlist_symbol()
        elif choice == "4":
            run_stock_scan("watchlist", "自選股分析")
        elif choice == "0":
            return
        else:
            print("請輸入 0-4。\n")


def show_watchlist(path: Path = WATCHLIST_PATH) -> list[str]:
    symbols = watchlist_symbols(path)
    print("")
    print(f"目前共有 {len(symbols)} 檔：")
    print("")
    if not symbols:
        print("尚未加入任何股票。")
        print("")
        return symbols

    for index, symbol in enumerate(symbols, start=1):
        print(f"{index}. {symbol}")
    print("")
    return symbols


def prompt_add_watchlist_symbol() -> None:
    symbol = input("請輸入股票代號（輸入 0 返回）：").strip()
    if symbol == "0":
        return
    try:
        added, count, normalized_symbol = add_watchlist_symbol(symbol)
    except ValueError as error:
        print(str(error))
        return

    if added:
        print(f"已新增：{normalized_symbol}")
        print(f"目前共有 {count} 檔股票")
    else:
        print("已存在於自選股。")


def prompt_remove_watchlist_symbol() -> None:
    symbols = show_watchlist()
    if not symbols:
        return

    choice = input("請選擇要刪除：").strip()
    if choice == "0":
        return
    if not choice.isdigit():
        print("請輸入列表中的數字。")
        return

    try:
        removed = remove_watchlist_index(int(choice))
    except IndexError as error:
        print(str(error))
        return

    print("已移除：")
    print(removed)


def show_project_status() -> None:
    status_path = Path("PROJECT_STATUS.md")
    print("\n[10] 查看專案狀態")
    print("------------------------------------")
    if not status_path.exists():
        print("找不到 PROJECT_STATUS.md\n")
    else:
        print(status_path.read_text(encoding="utf-8"))
        print("")
    wait_for_main_menu()


def show_menu() -> None:
    print("=========================================")
    print("      StockAnalyzerPro v3.0")
    print("         股票分析系統")
    print("=========================================")
    print("")
    print("【股票分析】")
    print("1. 分析單一股票")
    print("2. 分析自選股")
    print("3. 分析範例股票")
    print("")
    print("【歷史資料】")
    print("4. 更新 FinMind 財報")
    print("5. 建立歷史 SAP 評分")
    print("")
    print("【策略研究】")
    print("6. 執行策略回測")
    print("7. 比較策略績效")
    print("8. 產生研究報告")
    print("")
    print("【自選股管理】")
    print("9. 管理自選股")
    print("")
    print("【系統】")
    print("10. 查看專案狀態")
    print("0. 離開")
    print("")
    print("=========================================")


def main() -> None:
    while True:
        show_menu()
        choice = input("請選擇功能：").strip()

        if choice == "1":
            analyze_single_stock()
        elif choice == "2":
            run_stock_scan("watchlist", "自選股分析")
        elif choice == "3":
            run_stock_scan("sample", "範例股票分析")
        elif choice == "4":
            run_finmind_import()
        elif choice == "5":
            run_historical_sap_generator()
        elif choice == "6":
            run_cli("backtest.py", report_to_open=Path("reports/backtest_summary.md"))
        elif choice == "7":
            run_cli("strategy_compare.py", report_to_open=Path("reports/strategy_comparison.md"))
        elif choice == "8":
            run_cli("research_report.py", report_to_open=Path("reports/research_report.md"))
        elif choice == "9":
            manage_watchlist()
        elif choice == "10":
            show_project_status()
        elif choice == "0":
            print("已離開。")
            break
        else:
            print("請輸入 0-10。\n")


if __name__ == "__main__":
    main()
