import decimal
import pandas as pd
from typing import Protocol, Deque, List, Tuple
from binance.client import Client
from collections import deque
from threading import Lock
from binance.client import Client
from binance.ws.streams import ThreadedWebsocketManager
import logging

class BaseClient(Protocol):
    def get_system_status() -> dict:
        pass

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        pass

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        pass

    def get_current_price(self, symbol: str) -> decimal:
        pass

    def get_historical_data(self, symbol: str, interval: str, limit:int, start_str = None, end_str = None) -> pd.DataFrame:
        pass

    def get_last_trade(self) -> dict:
        pass

    def get_candles(self) -> List[List]:
        pass

    def get_position(self, symbol: str):
        pass

class BinanceClient(BaseClient):
    def __init__(self, api_key, api_secret, symbol: str, candles_window: int = 250):
        self.client = Client(api_key, api_secret)
        self.socket_manager = ThreadedWebsocketManager(api_key=api_key, api_secret=api_secret)
        self.symbol = symbol
        self.candles_window = candles_window
        self.candles: Deque[Tuple] = deque(maxlen=candles_window)
        self.lock = Lock()

        # Store trades for candle creation
        self.trades = []
        self.current_candle_time = None
        self.candles = []
        
        # Candle settings
        self.candle_interval = 10  # seconds

        self.start()
    
    def get_system_status(self):
        return self.client.get_system_status()

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        return self.client.order_market_buy(symbol=symbol, quoteOrderQty=quote_order_qty)

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        return self.client.order_limit_buy(symbol=symbol, price=str(price), quantity=quantity)

    def get_current_price(self, symbol: str) -> decimal:
        return self.client.get_symbol_ticker(symbol=symbol)

    def get_historical_data(self, symbol: str, interval: str = Client.KLINE_INTERVAL_1MINUTE, limit:int = 1000, start_str = None, end_str = None):
        return self.client.get_historical_klines(symbol=self.symbol, interval=interval, limit=limit, start_str=start_str, end_str=end_str)        

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

    def _trade_handler(self, msg):
        """Handle incoming trade messages"""
        try:
            # Extract trade data
            trade_time = pd.to_datetime(msg['T'], unit='ms')
            price = float(msg['p'])
            quantity = float(msg['q'])
            
            # Initialize candle time if needed
            if self.current_candle_time is None:
                self.current_candle_time = trade_time.floor('10S')
            
            # Check if we need to create a new candle
            if trade_time >= self.current_candle_time + pd.Timedelta(seconds=self.candle_interval):
                # Create candle from existing trades
                if self.trades:
                    self.create_candle()
                
                # Update candle time
                self.current_candle_time = trade_time.floor('10S')
            
            # Add trade to current window
            self.trades.append({
                'timestamp': trade_time,
                'price': price,
                'quantity': quantity
            })

            with self.lock:
                self.last_trade = msg
                            
        except Exception as e:
            logger.error(f"Error processing trade: {e}")

    def create_candle(self):
        """Create a candle from collected trades"""
        if not self.trades:
            return
        
        try:
            # Convert trades to DataFrame
            df = pd.DataFrame(self.trades)
            
            # Calculate OHLCV
            candle = {
                'timestamp': self.current_candle_time,
                'open': df.iloc[0]['price'],
                'high': df['price'].max(),
                'low': df['price'].min(),
                'close': df.iloc[-1]['price'],
                'volume': df['quantity'].sum(),
                'trades': len(df),
                'vwap': (df['price'] * df['quantity']).sum() / df['quantity'].sum()
            }
            
            self.candles.append(candle)
            self.trades = []  # Clear trades
            
            # Log candle
            logger.info(
                f"New candle: Time={candle['timestamp']}, "
                f"O={candle['open']:.2f}, H={candle['high']:.2f}, "
                f"L={candle['low']:.2f}, C={candle['close']:.2f}, "
                f"V={candle['volume']:.4f}"
            )
            
            return candle
            
        except Exception as e:
            logger.error(f"Error creating candle: {e}")
            self.trades = []  # Clear trades on error
    
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
            callback=self._trade_handler
        )
        self.socket_manager.start_kline_socket(
            symbol=self.symbol,
            callback=self._process_kline_message
        )