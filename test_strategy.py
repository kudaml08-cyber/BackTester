import queue

from data import HistoricCSVDataHandler
from strategy import MovingAverageCrossStrategy

events = queue.Queue()
bars = HistoricCSVDataHandler(events, "data", ["AAPL"])
strategy = MovingAverageCrossStrategy(bars, events, short_window=2, long_window=3)

while True:
    bars.update_bars()
    if not bars.continue_backtest:
        break

    # Process every event this bar created, in order
    while not events.empty():
        event = events.get()
        if event.type == "MARKET":
            strategy.calculate_signals(event)
        elif event.type == "SIGNAL":
            print(event.datetime.date(), event.symbol, event.signal_type)