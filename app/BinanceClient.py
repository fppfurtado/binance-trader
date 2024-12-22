import MarketClient
from binance.client import Client

class BinanceClient(MarketClient):
    
    def __init__(self, api_key, api_secret):
        self.client = Client(api_key, secret_key)
    
    def get_system_status():
        return self.client.get_system_status()

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        return self.client.order_market_buy(symbol=symbol, quoteOrderQty=quote_order_qty)

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        return self.client.order_limit_buy(symbol=symbol, price=price, quantity=quantity)