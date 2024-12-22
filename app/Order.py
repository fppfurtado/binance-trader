import time
import OrderType, OrderStatus
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