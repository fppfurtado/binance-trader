import decimal
from typing import Protocol, Deque, List, Tuple
from binance.client import Client
from collections import deque
from threading import Lock
from binance.client import Client
from binance.ws.streams import ThreadedWebsocketManager

class BaseClient(Protocol):
    def get_system_status() -> dict:
        pass

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        pass

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        pass

    def get_current_price(self, symbol: str) -> decimal:
        pass

    def get_historical_data(self, symbol: str, interval: str, period:int) -> []:
        pass

    def get_last_trade(self) -> dict:
        pass

    def get_candles(self) -> List[List]:
        pass

class BinanceClient(BaseClient):
    def __init__(self, api_key, api_secret, symbol: str, candles_window: int = 250):
        self.client = Client(api_key, api_secret)
        self.socket_manager = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
        self.symbol = symbol
        self.candles_window = candles_window
        self.candles: Deque[Tuple] = deque(maxlen=candles_window)
        self.lock = Lock()

        self.start()
    
    def get_system_status(self):
        return self.client.get_system_status()

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        return self.client.order_market_buy(symbol=symbol, quoteOrderQty=quote_order_qty)

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        return self.client.order_limit_buy(symbol=symbol, price=str(price), quantity=quantity)

    def get_current_price(self, symbol: str) -> decimal:
        return self.client.get_symbol_ticker(symbol=symbol)

    def get_historical_data(self, symbol: str, interval: str = Client.KLINE_INTERVAL_1MINUTE, limit:int = 50):
        return self.client.get_historical_klines(symbol=self.symbol, interval=interval, limit=limit)

    def _process_kline_message(self, msg: dict) -> None:
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

    def _process_trade_message(self, msg: dict) -> None:
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
            callback=self._process_trade_message
        )
        self.socket_manager.start_kline_socket(
            symbol=self.symbol,
            callback=self._process_kline_message
        )