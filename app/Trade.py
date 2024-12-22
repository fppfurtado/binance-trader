import decimal
import time
import TradeRole
import TradeSide
from dataclasses import dataclass

@dataclass
class Trade:
    time: time = time()
    symbol: str
    price: decimal
    quantity: decimal
    role: TradeRole
    baseAsset: str
    quoteAsset: str
    side: TradeSide
    feeAsset: str
    totalQuota: decimal