from backtest.engine import BacktestConfig, BacktestEngine
from backtest.portfolio import Portfolio
from backtest.report import BacktestReportWriter
from backtest.strategy import SAPScoreStrategy


def main() -> None:
    config = BacktestConfig()
    strategy = SAPScoreStrategy(
        min_sap_score=config.min_sap_score,
        min_piotroski_score=config.min_piotroski_score,
        min_data_quality_score=config.min_data_quality_score,
    )
    portfolio = Portfolio(initial_cash=config.initial_cash)
    engine = BacktestEngine(strategy=strategy, portfolio=portfolio, config=config)

    print("====================================")
    print(" StockAnalyzerPro Backtest MVP")
    print("====================================")
    print(f"期間：{config.start_date} 到 {config.end_date}")
    print(f"初始資金：{config.initial_cash}")
    print(f"Snapshot：{config.snapshot_path}")
    print("------------------------------------")

    result = engine.run()
    BacktestReportWriter().write(result)

    metrics = result["metrics"]
    print("------------------------------------")
    print("回測完成")
    print(f"Total Return：{metrics['total_return'] * 100:.2f}%")
    print(f"CAGR：{metrics['cagr'] * 100:.2f}%")
    print(f"Max Drawdown：{metrics['max_drawdown'] * 100:.2f}%")
    print(f"Win Rate：{metrics['win_rate'] * 100:.2f}%")
    print(f"Look-ahead-safe：{str(result['look_ahead_safe']).lower()}")
    print(f"Selected：{result['selected_stock_count']}")
    print(f"Skipped：{result['skipped_stock_count']}")
    print("Summary：reports\\backtest_summary.md")
    print("Equity Curve：reports\\backtest_equity_curve.csv")


if __name__ == "__main__":
    main()
