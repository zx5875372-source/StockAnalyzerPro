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
    print(" StockAnalyzerPro Backtest MVP")
    print("====================================")
    print(f"期間：{config.start_date} 到 {config.end_date}")
    print(f"初始資金：{config.initial_cash}")
    print(f"Benchmark：{config.benchmark_symbol}")
    print(f"Strategy：{strategy.name}")
    print(f"Snapshot：{config.resolved_snapshot_path()}")
    print(f"Universe：{config.universe_path}")
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
    print(f"Benchmark：{config.benchmark_symbol}")
    print(f"Benchmark Total Return：{format_cli_percent(metrics['benchmark_total_return'])}")
    print(f"Excess Return：{format_cli_percent(metrics['excess_return'])}")
    print(f"Strategy vs Benchmark：{metrics['strategy_vs_benchmark']}")
    print(f"Look-ahead-safe：{str(result['look_ahead_safe']).lower()}")
    print(f"Credibility：{result['credibility_grade']} - {result['credibility_reason']}")
    print(f"Selected：{result['selected_stock_count']}")
    print(f"Skipped：{result['skipped_stock_count']}")
    print("Summary：reports\\backtest_summary.md")
    print("Equity Curve：reports\\backtest_equity_curve.csv")


def format_cli_percent(value) -> str:
    if value is None:
        return "benchmark unavailable"
    return f"{value * 100:.2f}%"


if __name__ == "__main__":
    main()
