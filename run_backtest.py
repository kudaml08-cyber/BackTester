from backtest import Backtest
from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio
from strategy import MovingAverageCrossStrategy

bt = Backtest(
    csv_dir="data",
    symbol_list=["AAPL"],
    data_handler_cls=HistoricCSVDataHandler,
    strategy_cls=MovingAverageCrossStrategy,
    portfolio_cls=Portfolio,
    execution_cls=SimulatedExecutionHandler,
    strategy_params={"short_window": 2, "long_window": 3},
    portfolio_params={"initial_capital": 10000.0, "quantity": 50},
    execution_params={"slippage_pct": 0.01, "commission_pct": 0.001, "min_commission": 10.0},
)

df = bt.run()
print(df[["cash", "AAPL", "commission", "total", "returns"]])