class Event:
    """Base class. Exists so the loop can type-check events."""
    pass

class MarketEvent(Event):
    """New market bar is available."""
    def __init__(self):
        self.type = 'MARKET'

class SignalEvent(Event):
    """Strategy's opinion: go long/short/exit a symbol."""
    def __init__(self, symbol, datetime, signal_type, strength=1.0):
        self.type = 'SIGNAL'
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type  # 'LONG', 'SHORT', 'EXIT'
        self.strength = strength        # for scaling position size later

class OrderEvent(Event):
    """Portfolio's instruction: actually trade."""
    def __init__(self, symbol, order_type, quantity, direction):
        self.type = 'ORDER'
        self.symbol = symbol
        self.order_type = order_type    # 'MKT' or 'LMT'
        self.quantity = quantity
        self.direction = direction      # 'BUY' or 'SELL'

class FillEvent(Event):
    """What actually happened at the broker — including costs."""
    def __init__(self, timeindex, symbol, quantity, direction,
                 fill_price, commission):
        self.type = 'FILL'
        self.timeindex = timeindex
        self.symbol = symbol
        self.quantity = quantity
        self.direction = direction
        self.fill_price = fill_price
        self.commission = commission