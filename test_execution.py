import queue

from data import HistoricCSVDataHandler
from execution import SimulatedExecutionHandler
from portfolio import Portfolio
from strategy import MovingAverageCrossStrategy

events = queue.Queue()
bars = HistoricCSVDataHandler(events, "data", ["AAPL"])
strategy = MovingAverageCrossStrategy(bars, events, short_window=2, long_window=3)
portfolio = Portfolio(bars, events, initial_capital=10000.0, quantity=50)
broker = SimulatedExecutionHandler(bars, events, slippage_pct=0.01,
                                   commission_pct=0.001, min_commission=10.0)

while True:
    bars.update_bars()
    if not bars.continue_backtest:
        break

    while not events.empty():
        event = events.get()
        if event.type == "MARKET":
            broker.fill_pending_orders()        # 1. yesterday's orders fill at today's open
            strategy.calculate_signals(event)   # 2. then decide based on today's close
        elif event.type == "SIGNAL":
            portfolio.update_signal(event)
        elif event.type == "ORDER":
            broker.execute_order(event)
        elif event.type == "FILL":
            portfolio.update_fill(event)

    portfolio.update_timeindex()

df = portfolio.create_equity_dataframe()
print(df[["cash", "AAPL", "commission", "total", "returns"]])