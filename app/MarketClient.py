import decimal
import TradeSide, OrderType, OrderTime
from abc import ABC, abstractmethod

class MarketClient(ABC):


    @abstractmethod
    def get_system_status():
        return self.client.get_system_status()

    @abstractmethod
    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        return self.client.order_market_buy(symbol=symbol, quoteOrderQty=quote_order_qty)

    @abstractmethod
    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        return self.client.order_limit_buy(symbol=symbol, price=price, quantity=quantity)