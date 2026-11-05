import queue

from data import HistoricCSVDataHandler

events = queue.Queue()
data = HistoricCSVDataHandler(events, "data", ["AAPL"])

while True:
    data.update_bars()
    if not data.continue_backtest:
        break
    event = events.get()
    print(event.type,
          data.get_latest_bar_datetime("AAPL").date(),
          data.get_latest_bars_values("AAPL", "close", N=3))