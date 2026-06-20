from modules.downloader import get_stock_data
from modules.analyzer import analyze_stock
from modules.report import generate_markdown_report


def main():
    print("====================================")
    print(" StockAnalyzerPro v1.1")
    print("====================================")
    print("目前版本：v1.1 Validation & Backtesting Foundation")
    print("請輸入股票代號開始分析，例如 2330")
    print("輸入 q 離開")
    print("------------------------------------")

    while True:
        symbol = input("股票代號：").strip()

        if symbol.lower() == "q":
            print("已離開。")
            break

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


if __name__ == "__main__":
    main()
