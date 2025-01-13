from backtrader import Strategy, Order, Sizer
import analysis as a
from analysis import MarketTrend
from datetime import datetime
import numpy as np

class DefaultStrategy(Strategy):
    params = (
        ('max_orders', 400),     # Limite máximo de ordens abertas
    )

    def log(self, txt, dt=None, carriage_return=False):
        '''Logging function for the strategy'''
        dt = dt or self.datas[0].datetime.datetime()
        if not carriage_return:
            print('%s, %s' % (dt, txt))
        else:
            print('\r%s, %s' % (dt, txt))

    def __init__(self, binance, symbol: str = 'BTCUSDT', target_profit = 0.001):
        self.binance = binance
        self.symbol = symbol
        self.data = self.datas[0]
        self.dataclose = self.datas[0].close
        self.not_positioned_orders = {}  # Lista para armazenar ordens cuja compra não foi executada
        self.executed_buy_orders = []
        self.pending_sell_orders = []
        self.executed_sell_orders = []
        self.target_profit = target_profit
        self.total_profit = 0
        self.bar_executed = None
        self.trend = None
        self.safety_zone = None
        # self.sell_orders = []  # Lista para armazenar ordens de venda
        #self.orders = {}
        self._set_up_safety_zone()
 
    def next(self):

        # self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))

        bar_current = len(self)

        if self.bar_executed and bar_current >= self.bar_executed + 20:
            if len(self.not_positioned_orders) > 0:
                for ref, order in self.not_positioned_orders.items():
                    self.broker.cancel(order[0])
                self.not_positioned_orders.clear()
                self.log('************** ALL NOT POSITIONED ORDERS CANCELED! ************** ')
            self.bar_executed = None    
        
        match self.get_market_trend():
            case MarketTrend.HIGH:
                if self.trend != MarketTrend.HIGH:
                    self.log('******************* HIGH TREND *******************',carriage_return=True)
                    self.trend = MarketTrend.HIGH
                self.execute_high_trend_strategy()                 
            case MarketTrend.LOW:
                if self.trend != MarketTrend.LOW:
                    self.log('******************* LOW TREND *******************',carriage_return=True)
                    self.trend = MarketTrend.LOW
                # pass
            case MarketTrend.UNDEFINED:
                if self.trend != MarketTrend.UNDEFINED:
                    self.log('******************* UNDEFINED TREND *******************',carriage_return=True)
                    self.trend = MarketTrend.UNDEFINED                
                # pass

    def execute_high_trend_strategy(self):
        # current_price = float(self.binance.get_current_price(self.symbol)['price'])
        if  self.broker.cash > 0 and len(self.pending_sell_orders) < self.p.max_orders:
            self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))                
            current_price = self.dataclose[0]
            # discount = (0.05 / 100) * current_price
            # buy_price = current_price - discount
            buy_price = current_price
            main_order = self.buy(exectype=Order.Limit, price=buy_price, size=self._get_buy_size(self.p.max_orders),transmit=False)

            if main_order:
                #target_profit = (0.1 / 100) * main_order.price
                # target_profit = (0.1 / 100)
                sell_price = main_order.price * (1 + self.target_profit)
                # sell_price = current_price - 0.01
                take_profit_order = self.sell(parent=main_order, exectype=Order.Limit, price=sell_price, size=main_order.size, transmit=True, parent_price=main_order.price)
                self.pending_sell_orders.append(take_profit_order)                    
                self.not_positioned_orders.update({main_order.ref : (main_order, take_profit_order)})                    

            self.bar_executed = len(self)   

    def notify_order(self, order):
        #print(f'Ordem ref {order.ref}, Status {order.status}')
        if order.status == Order.Submitted:
            self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))
            self.log('ORDER SUBMITTED(%s, %s, %s, %s) = %.2f' % (order.ref, order.ordtype, order.price, order.size, order.size * order.price)) 
        # if order.status == Order.Accepted:
        #     if order.isbuy():
        #         self.not_positioned_orders.append(order)
        if order.status in [Order.Completed]:
            if order.isbuy():        
                self.log('BUY EXECUTED(%s, %s, %s) = %.2f' % (order.ref, order.executed.price, order.executed.size, order.executed.price*(order.executed.size)))
                self.not_positioned_orders.pop(order.ref)
                self.executed_buy_orders.append(order)
            #elif order.issell():
            if order.issell():
                self.log('SELL EXECUTED(%s, %s, %s) = %.2f' % (str(order.parent.ref)+"."+str(order.ref), order.executed.price, order.executed.size, order.executed.price*(-order.executed.size)))
                self.pending_sell_orders.remove(order)
                self.executed_sell_orders.append(order)
                self.total_profit = self.total_profit + (order.price - float(order.info['parent_price']))*(-order.size)
                
            self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))

            self.log(f'POSISION SIZE: {self.position.size}')
                
        if order.status == Order.Canceled:
                self.log('ORDER CANCELED(%s)' % (order.ref))
                if order.issell():
                    self.pending_sell_orders.remove(order)
                
    def get_market_trend(self) -> MarketTrend:
        if a.is_bullish(self._get_candle(-1)):
            if a.is_bullish(self._get_candle(-2)):
                return MarketTrend.HIGH
            else:
                return MarketTrend.UNDEFINED
        else:
            if a.is_bullish(self._get_candle(-2)):
                return MarketTrend.UNDEFINED
            else:
                return MarketTrend.LOW

    def _get_candle(self, index):
        return [
            self.data.datetime[index],
            self.data.open[index],
            self.data.high[index],
            self.data.low[index],
            self.data.close[index]
        ]

    def _get_buy_size(self, cash_divisor):
        # Fração do capital disponível
        cash_available = self.broker.get_cash() / cash_divisor
        size = cash_available / self.data.close[0]  # Quantidade baseada no preço de fechamento
        return size

    def _set_up_safety_zone(self):
        max_price = self.dataclose[0]
        price_offset = self._calculate_ranges_median()
        
        self.safety_zone = SafetyZone(max_price, price_offset)

    def _calculate_ranges_median(self):
        # Obtendo os candles mensais dos últimos 24 meses (períodos de 1 mês)
        candles = self.binance.get_klines(symbol='BTCUSDT', interval='1M', limit=24)

        # Extrair os ranges (high - low) de cada candle
        ranges = [float(candle[2]) - float(candle[3]) for candle in candles]

        # Calcular a mediana
        return np.median(ranges)

class SafetyZone:
    def __init__(self, max_price, price_offset):
        self._max_price = max_price
        self._price_offset = price_offset
        self.q1 = None
        self.q1 = None
        self.q3 = None

        self._calculate_quartiles()

    def _calculate_quartiles(self):
        self.q1 = self.min_price + (self._price_offset+1)/4
        self.q2 = self.min_price + (self._price_offset+1)/2
        self.q3 = self.min_price + (self._price_offset+1)/4*3

    @property
    def min_price(self):
        return self._max_price - self._price_offset

    @property
    def max_price(self):
        return self._max_price

    @max_price.setter
    def max_price(self, max_price):
        self._max_price = max_price
        self._calculate_quartiles()

    @property
    def price_offset(self):
        return self._price_offset

    @price_offset.setter
    def price_offset(self, price_offset):
        self._price_offset = price_offset
        self._calculate_quartiles()

    def __str__(self):
        header = f'========= SAFETY ZONE =========\n'
        max_price = f'Max Price: {self._max_price}\n'
        price_offset = f'Price Offset: {self._price_offset}\n'
        q1 = f'Q3: {self.q3}\n'
        q2  = f'Q2: {self.q2}\n'
        q3 = f'Q1: {self.q1}\n'
        min_price = f'Min Price: {self.min_price}\n'

        return header + max_price + price_offset + q1 + q2 + q3 + min_price