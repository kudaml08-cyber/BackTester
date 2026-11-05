from abc import ABC, abstractmethod
import os

import numpy as np
import pandas as pd

from events import MarketEvent


class DataHandler(ABC):
    """Interface every data source must follow (CSV now, live API later)."""

    @abstractmethod
    def get_latest_bar(self, symbol):
        raise NotImplementedError

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        raise NotImplementedError

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        raise NotImplementedError

    @abstractmethod
    def get_latest_bars_values(self, symbol, val_type, N=1):
        raise NotImplementedError

    @abstractmethod
    def update_bars(self):
        raise NotImplementedError


class HistoricCSVDataHandler(DataHandler):
    """Reads one CSV per symbol and drip-feeds bars like a live market."""

    def __init__(self, events, csv_dir, symbol_list):
        self.events = events                # the shared event queue
        self.csv_dir = csv_dir
        self.symbol_list = symbol_list
        self.symbol_data = {}               # symbol -> iterator over ALL bars (hidden future)
        self.latest_symbol_data = {}        # symbol -> list of bars released so far (the past)
        self.continue_backtest = True
        self._load_csv_files()

    def _load_csv_files(self):
        combined_index = None

        for s in self.symbol_list:
            path = os.path.join(self.csv_dir, f"{s}.csv")
            df = pd.read_csv(path, index_col="datetime", parse_dates=True).sort_index()
            self.symbol_data[s] = df
            self.latest_symbol_data[s] = []

            if combined_index is None:
                combined_index = df.index
            else:
                combined_index = combined_index.union(df.index)

        # Align every symbol to the same timeline, fill gaps with the last known
        # price, then turn each DataFrame into an iterator.
        for s in self.symbol_list:
            aligned = self.symbol_data[s].reindex(combined_index).ffill()
            self.symbol_data[s] = aligned.iterrows()

    def update_bars(self):
        """Release the next bar for every symbol, then announce it."""
        for s in self.symbol_list:
            try:
                bar = next(self.symbol_data[s])
            except StopIteration:
                self.continue_backtest = False
                return
            self.latest_symbol_data[s].append(bar)

        self.events.put(MarketEvent())

    def get_latest_bar(self, symbol):
        return self.latest_symbol_data[symbol][-1]

    def get_latest_bars(self, symbol, N=1):
        return self.latest_symbol_data[symbol][-N:]

    def get_latest_bar_datetime(self, symbol):
        return self.latest_symbol_data[symbol][-1][0]

    def get_latest_bars_values(self, symbol, val_type, N=1):
        bars = self.get_latest_bars(symbol, N)
        return np.array([bar[1][val_type] for bar in bars])