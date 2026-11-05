import queue

from data import HistoricCSVDataHandler
from events import FillEvent
from portfolio import Portfolio
from strategy import MovingAverageCrossStrategy

events = queue.Queue()
bars = HistoricCSVDataHandler(events, "data", ["AAPL"])
strategy = MovingAverageCrossStrategy(bars, events, short_window=2, long_window=3)
portfolio = Portfolio(bars, events, initial_capital=10000.0, quantity=50)

while True:
    bars.update_bars()
    if not bars.continue_backtest:
        break

    while not events.empty():
        event = events.get()
        if event.type == "MARKET":
            strategy.calculate_signals(event)
        elif event.type == "SIGNAL":
            portfolio.update_signal(event)
        elif event.type == "ORDER":
            # TEMPORARY fake broker: fills at today's close with no costs.
            # This is lookahead + zero costs. execution.py replaces it in step 5.
            price = bars.get_latest_bars_values(event.symbol, "close")[-1]
            dt = bars.get_latest_bar_datetime(event.symbol)
            events.put(FillEvent(dt, event.symbol, event.quantity,
                                 event.direction, price, 0.0))
        elif event.type == "FILL":
            portfolio.update_fill(event)

    portfolio.update_timeindex()   # snapshot once all of today's events are processed

df = portfolio.create_equity_dataframe()
print(df[["cash", "AAPL", "total", "returns"]])