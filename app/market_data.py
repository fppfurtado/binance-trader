import decimal
from typing import Protocol, Deque, List, Tuple
from binance.client import Client
from collections import deque
from threading import Lock

class BaseClient(Protocol):
    def get_system_status():
        pass

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        pass

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        pass

    def get_current_price(self, symbol: str) -> decimal:
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

    def get_current_price(self, symbol: str) -> decimal:
        return self.connector.get_symbol_ticker(symbol=symbol)

    def get_historical_data(self, symbol: str, interval: str, limit:int = 50):
        return self.connector.get_historical_klines(symbol=symbol, interval=interval, limit=limit)


class BaseWebsocket(Protocol):
    def get_last_trade(self):
        pass

    def get_candles(self) -> List[List]:
        pass

class BinanceWebsocket(BaseWebsocket):
    def __init__(self, symbol: str, socket_manager, max_length: int = 250):
        self.symbol = symbol
        self.socket_manager = socket_manager
        self.max_length = max_length
        self.candles: Deque[Tuple] = deque(maxlen=max_length)
        self.lock = Lock()
        
    def process_kline_message(self, msg: dict) -> None:
        if msg['e'] == 'kline' and msg['k']['i'] == '1m':
            candle = (
                msg['k']['t'], # timestamp
                msg['k']['o'], # open price
                msg['k']['c'], # close price
                msg['k']['h'], # high price
                msg['k']['l']  # low price
            )
            
            with self.lock:
                self.candles.append(candle)

    def process_trade_message(self, msg: dict) -> None:
        if msg['e'] == 'trade':  # Evento de trade (negociação)
            preco = (
                msg['E'],   # timestamp
                msg['p']    # Preço da negociação
            )
            
            with self.lock:
                self.last_trade = msg

    def get_last_trade(self) -> dict:
        with self.lock:
            return self.last_trade

    def get_closing_prices(self) -> List[float]:
        with self.lock:
            return [candle[2] for candle in self.candles]
            
    def get_candles(self) -> List[List]:
        with self.lock:
            return list(self.candles)

    def start(self) -> None:
        self.socket_manager.start()
        self.socket_manager.start_trade_socket(
            symbol=self.symbol,
            callback=self.process_trade_message
        )
        self.socket_manager.start_kline_socket(
            symbol=self.symbol,
            callback=self.process_kline_message
        )