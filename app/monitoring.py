from collections import deque
from threading import Lock
from typing import Deque, List, Tuple

class PriceMonitor:
    def __init__(self, symbol: str, socket_manager, max_length: int = 250):
        self.symbol = symbol
        self.socket_manager = socket_manager
        self.max_length = max_length
        self.candles: Deque[Tuple] = deque(maxlen=max_length)
        self.current_prices: Deque[Tuple] = deque(maxlen=max_length)
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
                self.current_prices.append(preco)

    def get_current_prices(self):
        with self.lock:
            return [price[1] for price in self.current_prices]

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
            symbol="BTCUSDT",
            callback=self.process_kline_message
        )