import pandas as pd

from events import OrderEvent


class Portfolio:
    """Tracks positions and cash, turns signals into orders, records equity each bar."""

    def __init__(self, bars, events, initial_capital=10000.0, quantity=50):
        self.bars = bars
        self.events = events
        self.symbol_list = bars.symbol_list
        self.initial_capital = initial_capital
        self.quantity = quantity                                  # fixed shares per trade (for now)

        self.current_positions = {s: 0 for s in self.symbol_list}  # shares held per symbol
        self.current_cash = initial_capital
        self.total_commission = 0.0
        self.equity_curve = []                                    # one snapshot per bar

    def update_signal(self, event):
        """Job 1: turn a SignalEvent into an OrderEvent, if it makes sense."""
        if event.type != "SIGNAL":
            return

        s = event.symbol
        held = self.current_positions[s]

        if event.signal_type == "LONG" and held == 0:
            price = self.bars.get_latest_bars_values(s, "close")[-1]
            affordable = int(self.current_cash // price)
            qty = min(self.quantity, affordable)
            if qty > 0:
                self.events.put(OrderEvent(s, "MKT", qty, "BUY"))

        elif event.signal_type == "EXIT" and held > 0:
            self.events.put(OrderEvent(s, "MKT", held, "SELL"))

    def update_fill(self, event):
        """Job 2: a trade happened, so update positions and cash."""
        if event.type != "FILL":
            return

        direction = 1 if event.direction == "BUY" else -1
        self.current_positions[event.symbol] += direction * event.quantity

        trade_value = direction * event.fill_price * event.quantity
        self.current_cash -= trade_value + event.commission
        self.total_commission += event.commission

    def update_timeindex(self):
        """Job 3: at the end of each bar, record what everything is worth."""
        dt = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        snapshot = {
            "datetime": dt,
            "cash": self.current_cash,
            "commission": self.total_commission,
        }

        market_value = 0.0
        for s in self.symbol_list:
            price = self.bars.get_latest_bars_values(s, "close")[-1]
            value = self.current_positions[s] * price
            snapshot[s] = value
            market_value += value

        snapshot["total"] = self.current_cash + market_value
        self.equity_curve.append(snapshot)

    def create_equity_dataframe(self):
        """Turn the snapshots into a table with daily returns."""
        df = pd.DataFrame(self.equity_curve).set_index("datetime")
        df["returns"] = df["total"].pct_change().fillna(0.0)
        df["equity_curve"] = (1.0 + df["returns"]).cumprod()
        return df