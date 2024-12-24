from binance.client import Client
from collections import deque
from threading import Lock
import pandas as pd
from typing import Deque, List
import time
from datetime import datetime, timedelta
from api_client import BaseClient

class PriceHistoryManager:
    def __init__(self, client: BaseClient, socket_manager, max_length: int = 250):
        self.client = client
        self.socket_manager = socket_manager
        self.max_length = max_length
        self.closing_prices: Deque[float] = deque(maxlen=max_length)
        self.timestamps: Deque[int] = deque(maxlen=max_length)
        self.lock = Lock()
        
    def _initialize_history(self) -> None:
        start_time = datetime.now() - timedelta(minutes=self.max_length)
        klines = self.client.get_historical_data(
            "BTCUSDT", 
            Client.KLINE_INTERVAL_1MINUTE,
            self.closing_prices.maxlen
        )
        
        with self.lock:
            for kline in klines[-300:]:
                self.timestamps.append(int(kline[0]))
                self.closing_prices.append(float(kline[4]))

    def process_message(self, msg: dict) -> None:
        if msg['e'] == 'kline' and msg['k']['i'] == '1m':
            timestamp = msg['k']['t']
            price = float(msg['k']['c'])
            
            with self.lock:
                if not self.timestamps or timestamp > self.timestamps[-1]:
                    self.timestamps.append(timestamp)
                    self.closing_prices.append(price)
                else:
                    self.closing_prices[-1] = price

    def get_closing_prices(self) -> List[float]:
        with self.lock:
            return list(self.closing_prices)

    def start(self) -> None:
        self._initialize_history()
        self.socket_manager.start()
        self.socket_manager.start_kline_socket(
            symbol="BTCUSDT",
            callback=self.process_message,
            interval=Client.KLINE_INTERVAL_1MINUTE
        )
        
    def stop(self) -> None:
        self.socket_manager.close()