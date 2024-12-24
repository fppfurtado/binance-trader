from abc import ABC, abstractclassmethod
import pandas as pd

class BaseIndicator(ABC):
    @abstractclassmethod
    def calculate(self, historical_data: []):
        pass

class ExponentialMovingAverage(BaseIndicator):
    def calculate(historical_data: [], period: int) -> float:
        return pd.Series(historical_data).ewm(span=period, adjust=False).mean().iloc[-1]