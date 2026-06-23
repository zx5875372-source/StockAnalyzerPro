from pathlib import Path
import subprocess
import sys

from modules.downloader import get_stock_data
from modules.analyzer import analyze_stock
from modules.report import generate_markdown_report
from scan import run_scan


def analyze_single_stock():
    print("\n[1] 分析單一股票")
    print("請輸入股票代號，例如 2330")
    print("輸入 q 返回主選單")
    print("------------------------------------")

    while True:
        symbol = input("請輸入股票代號：").strip()

        if symbol.lower() == "q":
            print("")
            return

        if not symbol:
            continue

        try:
            print("正在下載資料...")
            data = get_stock_data(symbol)
            print("正在分析...")
            result = analyze_stock(data)
            print("正在產生報告...")
            report_path = generate_markdown_report(result)

            print(f"\n分析完成：{result['symbol']}")
            print(f"SAP Score：{result['sap_score']} / 100")
            print(f"投資等級：{result['grade']}")
            print(f"報告已產生：{report_path}\n")

        except Exception as e:
            print(f"分析失敗：{e}\n")


def run_cli(script_name: str, args: list[str] | None = None) -> None:
    command = [sys.executable, script_name]
    if args:
        command.extend(args)
    print("")
    print(f"正在執行：{' '.join(command)}")
    print("------------------------------------")
    result = subprocess.run(command, check=False)
    if result.returncode == 0:
        print("完成")
    else:
        print(f"失敗（代碼：{result.returncode}）")
    print("")


def prompt_optional(label: str, default: str | None = None) -> str | None:
    suffix = f"（預設 {default}）" if default else "（可空白）"
    value = input(f"{label}{suffix}：").strip()
    if value:
        return value
    return default


def run_finmind_import():
    print("\n[4] 匯入 FinMind 財報")
    print("輸入 q 返回主選單")
    print("------------------------------------")
    symbol = input("請輸入股票代號：").strip()
    if symbol.lower() == "q":
        print("")
        return
    if not symbol:
        print("股票代號不可空白。\n")
        return

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

    run_cli("finmind_import.py", args)


def run_historical_sap_generator():
    print("\n[5] 建立歷史 SAP 評分")
    print("可留空代表處理全部財報快照")
    print("------------------------------------")
    db_path = prompt_optional("資料庫路徑", "historical_snapshots.db")
    symbol = prompt_optional("股票代號")
    year = prompt_optional("會計年度")
    quarter = prompt_optional("會計季度 1-4")

    args = []
    if db_path:
        args.extend(["--db", db_path])
    if symbol:
        args.extend(["--symbol", symbol])
    if year:
        args.extend(["--year", year])
    if quarter:
        args.extend(["--quarter", quarter])

    run_cli("historical_generate_sap.py", args)


def show_project_status():
    status_path = Path("PROJECT_STATUS.md")
    print("\n[9] 查看專案狀態")
    print("------------------------------------")
    if not status_path.exists():
        print("找不到 PROJECT_STATUS.md\n")
        return
    print(status_path.read_text(encoding="utf-8"))
    print("")


def show_menu():
    print("=========================================")
    print("      StockAnalyzerPro v2.4")
    print("          股票分析系統")
    print("=========================================")
    print("")
    print("【股票分析】")
    print("1. 分析單一股票")
    print("2. 分析自選股")
    print("3. 分析範例股票")
    print("")
    print("【歷史資料】")
    print("4. 匯入 FinMind 財報")
    print("5. 建立歷史 SAP 評分")
    print("")
    print("【策略研究】")
    print("6. 執行策略回測")
    print("7. 比較策略績效")
    print("8. 產生研究報告")
    print("")
    print("【系統】")
    print("9. 查看專案狀態")
    print("0. 離開")
    print("------------------------------------")


def main():
    while True:
        show_menu()
        choice = input("請選擇功能：").strip().lower()

        if choice == "1":
            analyze_single_stock()
        elif choice == "2":
            run_scan("watchlist")
            print("")
        elif choice == "3":
            run_scan("sample")
            print("")
        elif choice == "4":
            run_finmind_import()
        elif choice == "5":
            run_historical_sap_generator()
        elif choice == "6":
            run_cli("backtest.py")
        elif choice == "7":
            run_cli("strategy_compare.py")
        elif choice == "8":
            run_cli("research_report.py")
        elif choice == "9":
            show_project_status()
        elif choice in {"0", "q"}:
            print("已離開。")
            break
        else:
            print("請輸入 0-9，或 q 離開。\n")


if __name__ == "__main__":
    main()
