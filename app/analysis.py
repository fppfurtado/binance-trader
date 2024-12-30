from typing import Protocol, List, Tuple
import pandas as pd

def get_exponential_moving_average(historical_data: [], length: int) -> float:
    return -1 if len(historical_data) == 0 else pd.Series(historical_data).ewm(span=length, adjust=False).mean().iloc[-1]

def get_support_price(historical_data: [], window: int):
    print(f'TAMANHO: {len(historical_data[-window:])}')
    print(historical_data[-window:])
    return -1 if len(historical_data) <= window else min(candle[3] for candle in historical_data[-window:])