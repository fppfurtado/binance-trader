from typing import Protocol, List, Tuple
from enum import Enum
import pandas as pd

def get_exponential_moving_average(historical_data: [], length: int = None) -> float:
    if length is None:
        length = len(historical_data)
    
    return -1 if len(historical_data) == 0 else pd.Series(historical_data).ewm(span=length, adjust=False).mean().iloc[-1]

def get_support_price(historical_data: [], window: int = None):
    if window is None:
        window = len(historical_data)

    return -1 if len(historical_data) < window else min(candle[3] for candle in historical_data[-window:])

def is_bullish(candle: []):
    ''' candle: [timestamp, open, high, low, close, ...] '''
    return candle[4] > candle[1]

def is_bearish(candle: []):
    ''' candle: [timestamp, open, high, low, close, ...] '''
    return candle[4] < candle[1]

class MarketTrend(Enum):
    HIGH = 'HIGH'
    LOW = 'LOW'
    UNDEFINED = 'UNDEFINED'