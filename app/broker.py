import decimal
import time
from datetime import datetime
import pandas as pd
from typing import Protocol, Deque, List, Tuple
from binance.client import Client
from collections import deque
from threading import Lock
from binance.client import Client
from binance.ws.streams import ThreadedWebsocketManager
import logging
import numpy as np

class BaseClient(Protocol):
    logger = logging.getLogger('trader')

    def get_system_status() -> dict:
        pass

    def order_market_buy(self, symbol: str, quote_order_qty: decimal):
        pass

    def order_limit_buy(self, symbol: str, price: decimal, quantity: decimal):
        pass

    def get_current_price(self, symbol: str) -> decimal:
        pass

    def get_klines(self, symbol: str, interval: str, limit:int, start_time: datetime, end_time: datetime):
        pass

    def get_10s_klines(self, symbol: str, start_time, end_time=None):
        pass

    def get_last_trade(self) -> dict:
        pass

    def get_candles(self) -> List[List]:
        pass

    def get_position(self, symbol: str):
        pass

    def get_price_difference_median(interval, period):
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

    def get_klines(self, symbol: str, interval: str = Client.KLINE_INTERVAL_1MINUTE, limit:int = 1000, start_time: datetime = None, end_time: datetime = None):
        if start_time and end_time:
            """
            Fetch 1s klines and aggregate them to 10s klines
            
            Parameters:
            - symbol: Trading pair (e.g., 'BTCUSDT')
            - start_time: Start time in datetime format
            - end_time: End time in datetime format (default: current time)
            """
            # Convert times to milliseconds timestamp
            start_ts = int(start_time.timestamp() * 1000)
            if end_time is None:
                end_time = datetime.now()
            end_ts = int(end_time.timestamp() * 1000)
            
            all_klines = []
            current_ts = start_ts
            
            self.logger.info(f"Fetching 1s klines for {symbol} from {start_time} to {end_time}")
            
            while current_ts < end_ts:
                try:
                    # Fetch batch of 1s klines (1000 is the maximum limit per request)
                    klines = self.client.get_klines(
                        symbol=symbol,
                        interval=interval,
                        startTime=current_ts,
                        endTime=min(current_ts + (1000 * 1000), end_ts),  # 1s * 1000 candles
                        limit=1000
                    )
                    
                    if not klines:
                        self.logger.info("No more klines found")
                        break
                        
                    # Process klines
                    for k in klines:
                        kline_data = {
                            'timestamp': datetime.fromtimestamp(k[0] / 1000),
                            'open': float(k[1]),
                            'high': float(k[2]),
                            'low': float(k[3]),
                            'close': float(k[4]),
                            'volume': float(k[5]),
                            'close_time': datetime.fromtimestamp(k[6] / 1000)
                            # 'quote_volume': float(k[7]),
                            # 'trades': int(k[8]),
                            # 'taker_buy_volume': float(k[9]),
                            # 'taker_buy_quote_volume': float(k[10])
                        }
                        all_klines.append(kline_data)
                    
                    # Update timestamp for next batch
                    current_ts = klines[-1][6] + 1
                    
                    # Print progress
                    progress = (current_ts - start_ts) / (end_ts - start_ts) * 100
                    print(f"\rProgress: {progress:.2f}% - Klines collected: {len(all_klines)}", end='')
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.logger.error(f"\nError fetching klines: {e}")
                    time.sleep(1)
                    continue
            
            self.logger.info("\nKline collection completed")
            
            return all_klines     
        else:
            return self.client.get_klines(symbol=self.symbol, interval=interval, limit=limit)

    def get_10s_klines(self, symbol, start_time, end_time=None):
        """
        Fetch 1s klines and aggregate them to 10s klines
        
        Parameters:
        - symbol: Trading pair (e.g., 'BTCUSDT')
        - start_time: Start time in datetime format
        - end_time: End time in datetime format (default: current time)
        """
        # Convert times to milliseconds timestamp
        start_ts = int(start_time.timestamp() * 1000)
        if end_time is None:
            end_time = datetime.now()
        end_ts = int(end_time.timestamp() * 1000)
        
        all_klines = []
        current_ts = start_ts
        
        self.logger.info(f"Fetching 1s klines for {symbol} from {start_time} to {end_time}")
        
        while current_ts < end_ts:
            try:
                # Fetch batch of 1s klines (1000 is the maximum limit per request)
                klines = self.client.get_klines(
                    symbol=symbol,
                    interval=Client.KLINE_INTERVAL_1SECOND,
                    startTime=current_ts,
                    endTime=min(current_ts + (1000 * 1000), end_ts),  # 1s * 1000 candles
                    limit=1000
                )
                
                if not klines:
                    self.logger.info("No more klines found")
                    break
                    
                # Process klines
                for k in klines:
                    kline_data = {
                        'timestamp': datetime.fromtimestamp(k[0] / 1000),
                        'open': float(k[1]),
                        'high': float(k[2]),
                        'low': float(k[3]),
                        'close': float(k[4]),
                        'volume': float(k[5]),
                        'close_time': datetime.fromtimestamp(k[6] / 1000)
                        # 'quote_volume': float(k[7]),
                        # 'trades': int(k[8]),
                        # 'taker_buy_volume': float(k[9]),
                        # 'taker_buy_quote_volume': float(k[10])
                    }
                    all_klines.append(kline_data)
                
                # Update timestamp for next batch
                current_ts = klines[-1][6] + 1
                
                # Print progress
                progress = (current_ts - start_ts) / (end_ts - start_ts) * 100
                self.logger.info(f"\rProgress: {progress:.2f}% - Klines collected: {len(all_klines)}")
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                self.logger.error(f"\nError fetching klines: {e}")
                time.sleep(1)
                continue
        
        self.logger.info("\nKline collection completed")
        
        # Convert to DataFrame
        df = pd.DataFrame(all_klines)
        
        # Create 10-second groups
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['10s_group'] = df['timestamp'].dt.floor('10s')
        df.set_index('timestamp', inplace=True)
        
        # Aggregate to 10-second klines
        agg_dict = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
            # 'quote_volume': 'sum',
            # 'trades': 'sum',
            # 'taker_buy_volume': 'sum',
            # 'taker_buy_quote_volume': 'sum'
        }
        
        # df_10s = df.groupby('10s_group').agg(agg_dict).reset_index()
        df_10s = df.groupby('10s_group').agg(agg_dict)
        df_10s = df_10s.rename(columns={'10s_group': 'timestamp'})
        
        return df_10s     

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
                self.current_candle_time = trade_time.floor('10s')
            
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
            self.logger.error(f"Error processing trade: {e}")

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
            self.logger.info(
                f"New candle: Time={candle['timestamp']}, "
                f"O={candle['open']:.2f}, H={candle['high']:.2f}, "
                f"L={candle['low']:.2f}, C={candle['close']:.2f}, "
                f"V={candle['volume']:.4f}"
            )
            
            return candle
            
        except Exception as e:
            self.logger.error(f"Error creating candle: {e}")
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
        # self.socket_manager.start_trade_socket(
        #     symbol=self.symbol,
        #     callback=self._trade_handler
        # )
        self.socket_manager.start_kline_socket(
            symbol=self.symbol,
            callback=self._process_kline_message
        )

    def get_price_difference_median(self, interval, period = 1000):
        # Obtendo os candles mensais dos últimos 24 meses (períodos de 1 mês)
        candles = self.get_klines(symbol=self.symbol, interval=interval, limit=period)

        # Extrair os ranges (high - low) de cada candle
        ranges = [float(candle[2]) - float(candle[3]) for candle in candles]

        # Calcular a mediana
        return np.median(ranges)