import time
from dataclasses import dataclass

@dataclass
class Order:
    order_id: int
    time: time = time()
    order_type: OrderType
    trade_side: TradeSide
    status: OrderStatus = OrderStatus.NEW
    base_asset: str
    quote_asset: str
    price: decimal
    orig_qty: decimal
    executed_price: decimal
    executed_qty: decimal
    executed_quote: decimal
    delegate_money: decimal
    
    @property
    def symbol(self):
        return self.base_asset + self.quote_asset

class OrderType(Enum):
    LIMIT = 'LIMIT'
    MARKET = 'MARKET'

class OrderStatus(Enum):
    NEW = 'NEW'
    FILLED = 'FILLED'
    CANCELED = 'CANCELED'

class OrderTime(Enum):
    GOOD_TIL_CANCELED = 'GTC'
    IMMEDIATE_OR_CANCEL = 'IOC'
    FILL_OR_KILL = 'FOK'
    GOOD_TIL_CROSS = 'GTX'