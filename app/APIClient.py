import decimal
from abc import ABC, abstractmethod
from binance.client import Client

class BaseClient(ABC):

    @abstractmethod
    def get_system_status():
        pass

    @abstractmethod
    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        pass

    @abstractmethod
    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        pass

class BinanceClient(BaseClient):
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, api_secret)
    
    def get_system_status(self):
        return self.client.get_system_status()

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        return self.client.order_market_buy(symbol=symbol, quoteOrderQty=quote_order_qty)

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        return self.client.order_limit_buy(symbol=symbol, price=str(price), quantity=quantity)