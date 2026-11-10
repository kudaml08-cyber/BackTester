import queue


class Backtest:
    """Wires all the components to one shared queue and runs the event loop."""

    def __init__(self, csv_dir, symbol_list,
                 data_handler_cls, strategy_cls, portfolio_cls, execution_cls,
                 strategy_params=None, portfolio_params=None, execution_params=None):
        self.events = queue.Queue()

        # Build every component around the SAME queue and the SAME data handler
        self.bars = data_handler_cls(self.events, csv_dir, symbol_list)
        self.strategy = strategy_cls(self.bars, self.events, **(strategy_params or {}))
        self.portfolio = portfolio_cls(self.bars, self.events, **(portfolio_params or {}))
        self.broker = execution_cls(self.bars, self.events, **(execution_params or {}))

        # Counters: a quick sanity check on every run
        self.num_bars = 0
        self.num_signals = 0
        self.num_orders = 0
        self.num_fills = 0

    def _run_loop(self):
        while True:
            self.bars.update_bars()
            if not self.bars.continue_backtest:
                break
            self.num_bars += 1

            while not self.events.empty():
                event = self.events.get()
                if event.type == "MARKET":
                    self.broker.fill_pending_orders()        # open: fill yesterday's orders
                    self.strategy.calculate_signals(event)   # close: decide
                elif event.type == "SIGNAL":
                    self.num_signals += 1
                    self.portfolio.update_signal(event)
                elif event.type == "ORDER":
                    self.num_orders += 1
                    self.broker.execute_order(event)
                elif event.type == "FILL":
                    self.num_fills += 1
                    self.portfolio.update_fill(event)

            self.portfolio.update_timeindex()

    def run(self):
        self._run_loop()

        if self.broker.pending_orders:
            print(f"Warning: {len(self.broker.pending_orders)} order(s) never filled - data ended first.")

        print(f"Bars: {self.num_bars} | Signals: {self.num_signals} | "
              f"Orders: {self.num_orders} | Fills: {self.num_fills}")

        return self.portfolio.create_equity_dataframe()