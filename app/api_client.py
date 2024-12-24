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

    def get_historical_data(self, symbol: str, interval: str, period:int):
        pass

class BinanceClient(BaseClient):
    def __init__(self, api_key, api_secret):
        self.connector = Client(api_key, api_secret)
    
    def get_system_status(self):
        return self.connector.get_system_status()

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        return self.connector.order_market_buy(symbol=symbol, quoteOrderQty=quote_order_qty)

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        return self.connector.order_limit_buy(symbol=symbol, price=str(price), quantity=quantity)

    def get_historical_data(self, symbol: str, interval: str, limit:int = 50):
        return self.connector.get_historical_klines(symbol=symbol, interval=interval, limit=limit)