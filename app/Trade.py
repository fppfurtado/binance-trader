import time
import decimal
from dataclasses import dataclass

@dataclass
class Trade:
    time: time = time()
    side: TradeSide
    role: TradeRole
    base_asset: str
    quote_asset: str
    price: decimal
    quantity: decimal
    fee_asset: str
    total_quota: decimal

    @property
    def symbol(self):
        return self.base_asset + self.quote_asset

class TradeRole(Enum):
    MAKER = 'Maker'
    TAKER = 'Taker'

class TradeSide(Enum):
    BUY = 'BUY'
    SELL = 'SELL'