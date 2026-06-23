from backtest.cli import build_config_from_args, create_parser
from backtest.engine import BacktestEngine
from backtest.portfolio import Portfolio
from backtest.report import BacktestReportWriter
from strategy.registry import create_default_registry


def main(argv=None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        config = build_config_from_args(args)
    except ValueError as error:
        parser.error(str(error))

    registry = create_default_registry()
    strategy = registry.get(
        config.strategy_name,
        min_sap_score=config.min_sap_score,
        min_piotroski_score=config.min_piotroski_score,
        min_data_quality_score=config.min_data_quality_score,
    )
    portfolio = Portfolio(initial_cash=config.initial_cash)
    engine = BacktestEngine(strategy=strategy, portfolio=portfolio, config=config)

    print("====================================")
    print(" StockAnalyzerPro 策略回測")
    print("====================================")
    print(f"期間：{config.start_date} 到 {config.end_date}")
    print(f"初始資金：{config.initial_cash}")
    print(f"基準指數：{config.benchmark_symbol}")
    print(f"策略：{strategy.name}")
    print(f"快照來源：{config.resolved_snapshot_label()}")
    print(f"股票範圍：{config.universe_path}")
    print("------------------------------------")

    print("正在執行回測...")
    result = engine.run()
    print("正在產生報告...")
    BacktestReportWriter().write(result)

    metrics = result["metrics"]
    print("------------------------------------")
    print("回測完成")
    print(f"總報酬率：{metrics['total_return'] * 100:.2f}%")
    print(f"年化報酬率：{metrics['cagr'] * 100:.2f}%")
    print(f"最大回撤：{metrics['max_drawdown'] * 100:.2f}%")
    print(f"勝率：{metrics['win_rate'] * 100:.2f}%")
    print(f"基準指數：{config.benchmark_symbol}")
    print(f"基準總報酬率：{format_cli_percent(metrics['benchmark_total_return'])}")
    print(f"超額報酬率：{format_cli_percent(metrics['excess_return'])}")
    print(f"是否勝過基準：{format_cli_benchmark_result(metrics['strategy_vs_benchmark'])}")
    print(f"無未來函數：{str(result['look_ahead_safe']).lower()}")
    print(f"可信度：{result['credibility_grade']} - {result['credibility_reason']}")
    print(f"入選股票：{result['selected_stock_count']}")
    print(f"略過股票：{result['skipped_stock_count']}")
    print("摘要報告：reports\\backtest_summary.md")
    print("權益曲線：reports\\backtest_equity_curve.csv")
    print("回測資格 CSV：reports\\backtest_qualification.csv")
    print("回測資格 JSON：reports\\backtest_qualification.json")


def format_cli_percent(value) -> str:
    if value is None:
        return "基準資料不足"
    return f"{value * 100:.2f}%"


def format_cli_benchmark_result(value: str) -> str:
    if value == "outperform":
        return "是"
    if value == "underperform":
        return "否"
    return "基準資料不足"


if __name__ == "__main__":
    main()
