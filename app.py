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
        symbol = input("股票代號：").strip()

        if symbol.lower() == "q":
            print("")
            return

        if not symbol:
            continue

        try:
            data = get_stock_data(symbol)
            result = analyze_stock(data)
            report_path = generate_markdown_report(result)

            print(f"\n分析完成：{result['symbol']}")
            print(f"SAP Score：{result['sap_score']} / 100")
            print(f"投資等級：{result['grade']}")
            print(f"報告位置：{report_path}\n")

        except Exception as e:
            print(f"分析失敗：{e}\n")


def show_menu():
    print("====================================")
    print(" StockAnalyzerPro v1.4")
    print("====================================")
    print("目前版本：v1.4 CLI UX Improvement")
    print("[1] 分析單一股票")
    print("[2] 掃描自選股 watchlist")
    print("[3] 掃描 sample stocks")
    print("[4] 離開")
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
        elif choice in {"4", "q"}:
            print("已離開。")
            break
        else:
            print("請輸入 1、2、3 或 4。\n")


if __name__ == "__main__":
    main()
