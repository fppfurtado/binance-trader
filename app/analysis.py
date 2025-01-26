from typing import Protocol, List, Tuple
from enum import Enum
import pandas as pd
import backtrader as bt

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

class ProfitReturns(bt.Analyzer):
    def __init__(self):
        super(ProfitReturns, self).__init__()
        # self.initial_profit = None
        # self.final_profit = None
        # self.profit_returns = []
        # self.total_profit = 0

    def start(self):
        # Armazenando o valor inicial do caixa no início do backtest
        # self.initial_profit = self.strategy.broker.startingcash
        pass

    def next(self):
        # Armazenando o valor do caixa a cada passo do backtest
        # self.profit_returns.append(self.strategy.broker.get_cash())
        pass

    def stop(self):
        # O valor final do caixa no final do backtest
        self.total_profit = round((self.strategy.total_profit / self.strategy.p.stake) * 100, 1)

    def get_analysis(self):
        # Calculando o retorno com base na evolução do caixa
        return {
            'total_profit': self.total_profit,
        }

class TradeCounter(bt.Analyzer):
    def __init__(self):
        super(TradeCounter, self).__init__()
        # self.initial_profit = None
        # self.final_profit = None
        # self.profit_returns = []
        # self.total_profit = 0

    def start(self):
        # Armazenando o valor inicial do caixa no início do backtest
        # self.initial_profit = self.strategy.broker.startingcash
        pass

    def next(self):
        # Armazenando o valor do caixa a cada passo do backtest
        # self.profit_returns.append(self.strategy.broker.get_cash())
        pass

    def stop(self):
        # O valor final do caixa no final do backtest
        self.total_trades = self.strategy.executed_sell_orders_counter

    def get_analysis(self):
        # Calculando o retorno com base na evolução do caixa
        return {
            'total_trades': self.total_trades,
        }

class LastDate(bt.Analyzer):
    def __init__(self):
        super(LastDate, self).__init__()
        # self.initial_profit = None
        # self.final_profit = None
        # self.profit_returns = []
        # self.total_profit = 0

    def start(self):
        # Armazenando o valor inicial do caixa no início do backtest
        # self.initial_profit = self.strategy.broker.startingcash
        pass

    def next(self):
        # Armazenando o valor do caixa a cada passo do backtest
        # self.profit_returns.append(self.strategy.broker.get_cash())
        pass

    def stop(self):
        # O valor final do caixa no final do backtest
        self.date = self.strategy.last_trade_date

    def get_analysis(self):
        # Calculando o retorno com base na evolução do caixa
        return {
            'last_date': self.date,
        }