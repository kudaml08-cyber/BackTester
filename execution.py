from abc import ABC, abstractmethod

from events import FillEvent


class ExecutionHandler(ABC):
    """Interface every broker (simulated or real) must follow."""

    @abstractmethod
    def execute_order(self, event):
        raise NotImplementedError


class SimulatedExecutionHandler(ExecutionHandler):
    """Fills orders at the NEXT bar's open, with slippage and commission."""

    def __init__(self, bars, events, slippage_pct=0.0005,
                 commission_pct=0.001, min_commission=10.0):
        self.bars = bars
        self.events = events
        self.slippage_pct = slippage_pct        # 0.0005 = 0.05% worse price per trade
        self.commission_pct = commission_pct    # 0.001  = 0.1% of trade value
        self.min_commission = min_commission    # but never less than this per trade
        self.pending_orders = []                # orders waiting for the next open

    def execute_order(self, event):
        """Accept an order now. It gets filled when the next bar opens."""
        if event.type == "ORDER":
            self.pending_orders.append(event)

    def fill_pending_orders(self):
        """Call at the start of each new bar: fill waiting orders at today's open."""
        for order in self.pending_orders:
            open_price = self.bars.get_latest_bars_values(order.symbol, "open")[-1]
            dt = self.bars.get_latest_bar_datetime(order.symbol)

            # Slippage always works against you
            if order.direction == "BUY":
                fill_price = open_price * (1 + self.slippage_pct)
            else:
                fill_price = open_price * (1 - self.slippage_pct)

            trade_value = fill_price * order.quantity
            commission = max(self.min_commission, self.commission_pct * trade_value)

            self.events.put(FillEvent(dt, order.symbol, order.quantity,
                                      order.direction, fill_price, commission))

        self.pending_orders = []