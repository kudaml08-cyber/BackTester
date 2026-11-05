from abc import ABC, abstractmethod

from events import SignalEvent


class Strategy(ABC):
    """Interface every strategy must follow."""

    @abstractmethod
    def calculate_signals(self, event):
        raise NotImplementedError


class MovingAverageCrossStrategy(Strategy):
    """LONG when the short SMA crosses above the long SMA, EXIT when it crosses below."""

    def __init__(self, bars, events, short_window=2, long_window=3):
        self.bars = bars                    # the DataHandler (only source of prices)
        self.events = events                # the shared event queue
        self.symbol_list = bars.symbol_list
        self.short_window = short_window
        self.long_window = long_window
        # What this strategy last SAID for each symbol: 'OUT' or 'LONG'
        self.state = {s: "OUT" for s in self.symbol_list}

    def calculate_signals(self, event):
        if event.type != "MARKET":
            return

        for s in self.symbol_list:
            closes = self.bars.get_latest_bars_values(s, "close", N=self.long_window)

            # Not enough history yet to compute the long average
            if len(closes) < self.long_window:
                continue

            short_sma = closes[-self.short_window:].mean()
            long_sma = closes.mean()
            dt = self.bars.get_latest_bar_datetime(s)

            if short_sma > long_sma and self.state[s] == "OUT":
                self.events.put(SignalEvent(s, dt, "LONG"))
                self.state[s] = "LONG"

            elif short_sma < long_sma and self.state[s] == "LONG":
                self.events.put(SignalEvent(s, dt, "EXIT"))
                self.state[s] = "OUT"