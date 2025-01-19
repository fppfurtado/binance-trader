from backtrader import Strategy, Order, Sizer
import analysis as a
from analysis import MarketTrend
from datetime import datetime
import numpy as np

class DefaultStrategy(Strategy):
    params = (
        ('max_pending_sell_orders', 1),     # Limite máximo de operações abertas
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
        self.stake_per_order = self.broker.cash / self.p.max_pending_sell_orders
        self.not_positioned_operations = {}  # Lista para armazenar ordens cuja compra não foi executada
        self.executed_buy_orders = []
        self.pending_sell_orders = []
        self.executed_sell_orders = []
        self.target_profit = target_profit
        self.total_profit = 0
        self.bar_executed = None
        self.trend = None
        self.safety_zone = None
        self.trend_counters = [0, 0, 0]
        self.max_price = 0
        # self.sell_orders = []  # Lista para armazenar ordens de venda
        #self.orders = {}
        # self._set_up_safety_zone(4)
        self.fisrt_zone = self.safety_zone.__str__()
 
    def next(self):

        # self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))
        bar_current = len(self)
        current_price = self.dataclose[0]

        if current_price > self.max_price:
            self.max_price = current_price

        if self.safety_zone:
                if current_price > (self.safety_zone.max_price + self.safety_zone.price_offset * 0.1) or current_price < self.safety_zone.min_price:
                    self.safety_zone.max_price = current_price

        if current_price <= self.max_price * (1 - self.target_profit/10):

            match self.get_market_trend():
                # buy_sig
                case MarketTrend.HIGH:
                    if self.trend != MarketTrend.HIGH:
                        # self.log(f'******************* HIGH TREND ******************* {self.dataclose[0]}')
                        self.trend = MarketTrend.HIGH
                    self.trend_counters[0] += 1
                    # self.execute_high_trend_strategy(bar_current, current_price)
                case MarketTrend.LOW:
                    if self.trend != MarketTrend.LOW:
                        # self.log(f'******************* LOW TREND ******************* {self.dataclose[0]}')
                        self.trend = MarketTrend.LOW
                    self.trend_counters[1] += 1
                    # pass
                case MarketTrend.UNDEFINED:
                    if self.trend != MarketTrend.UNDEFINED:
                        # self.log(f'******************* UNDEFINED TREND ******************* {self.dataclose[0]}')
                        self.trend = MarketTrend.UNDEFINED                
                    self.trend_counters[2] += 1
                    self.execute_high_trend_strategy(bar_current, current_price)
                    # for i in range(self.p.max_pending_sell_orders):
                    #     self.execute_high_trend_strategy(bar_current, current_price)
                    # pass

    def execute_high_trend_strategy(self, bar_current, current_price):

        if self.bar_executed and bar_current >= self.bar_executed + 400:
            if len(self.not_positioned_operations) > 0:
                for ref, order in self.not_positioned_operations.items():
                    self.broker.cancel(order[0])
                self.not_positioned_operations.clear()
                self.log('************** ALL NOT POSITIONED ORDERS CANCELED! ************** ')
            self.bar_executed = None            

        # current_price = float(self.binance.get_current_price(self.symbol)['price'])
        if  self.broker.cash > 0 and len(self.pending_sell_orders) < self.p.max_pending_sell_orders:
            if self.safety_zone:
                if current_price > self.safety_zone.max_price:
                    self.make_operation(current_price, -1)
                else:
                    for index, range in enumerate(self.safety_zone.price_ranges):
                        if (current_price > self.safety_zone.max_price or range[0] <= current_price < range[1]) and self.safety_zone.counters[index] < self.p.max_pending_sell_orders/4:
                                self.make_operation(current_price, index)                                           
            else:
                self.make_operation(current_price, None)

            self.bar_executed = len(self)

    def make_operation(self, current_price, index):
        buy_price = current_price * (1 - self.target_profit/2)
        main_order = self.buy(exectype=Order.Limit, price=buy_price, size=self.stake_per_order/buy_price,transmit=False)

        if main_order:
            position = main_order.price * main_order.size
            sell_price = (position + (self.stake_per_order * self.target_profit))/main_order.size

            if index:
                take_profit_order = self.sell(parent=main_order, exectype=Order.Limit, price=sell_price, size=main_order.size, transmit=True, parent_price=main_order.price, range_index=index)
                self.safety_zone.increase_range_counter(index)                        
            else:
                take_profit_order = self.sell(parent=main_order, exectype=Order.Limit, price=sell_price, size=main_order.size, transmit=True, parent_price=main_order.price, range_index=None)
                    
            self.pending_sell_orders.append(take_profit_order)                    
            self.not_positioned_operations.update({main_order.ref : (main_order, take_profit_order)})

    def notify_order(self, order):
        #print(f'Ordem ref {order.ref}, Status {order.status}')
        if order.status == Order.Submitted:
            # pass
            self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))            
            self.log('ORDER SUBMITTED(%s, %s, %s, %s) = %.2f' % (order.ref, order.ordtype, order.price, order.size, order.size * order.price)) 
        # if order.status == Order.Accepted:
        #     if order.isbuy():
        #         self.not_positioned_operations.append(order)
        if order.status in [Order.Completed]:
            self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))            
            if order.isbuy():        
                self.log('BUY EXECUTED(%s, %s, %s) = %.2f' % (order.ref, order.executed.price, order.executed.size, order.executed.price*(order.executed.size)))
                self.not_positioned_operations.pop(order.ref)
                self.executed_buy_orders.append(order)
            #elif order.issell():
            if order.issell():
                self.log('SELL EXECUTED(%s, %s, %s) = %.2f' % (str(order.parent.ref)+"."+str(order.ref), order.executed.price, order.executed.size, order.executed.price*(-order.executed.size)))
                self.pending_sell_orders.remove(order)
                self.executed_sell_orders.append(order)
                self.total_profit = self.total_profit + (order.price - float(order.info['parent_price']))*(-order.size)
                if self.safety_zone:
                    self.safety_zone.decrease_range_counter(order.info['range_index'])
                
            # self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))

            self.log(f'POSISION SIZE: {self.position.size}')
                
        if order.status == Order.Canceled:
                self.log('ORDER CANCELED(%s)' % (order.ref))
                if order.issell():
                    self.pending_sell_orders.remove(order)
                    if self.safety_zone:
                        self.safety_zone.decrease_range_counter(order.info['range_index'])
             
    def get_market_trend(self) -> MarketTrend:
        if a.is_bullish(self._get_candle(0)):
            if a.is_bullish(self._get_candle(-1)):
                return MarketTrend.HIGH
            else:
                return MarketTrend.UNDEFINED
        else:
            if a.is_bullish(self._get_candle(-1)):
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

    def _set_up_safety_zone(self, n_ranges):
        max_price = self.dataclose[0]
        price_offset = self._calculate_timeframe_range_limits()
        
        self.safety_zone = SafetyZone(max_price, price_offset, n_ranges)

class SafetyZone:
    def __init__(self, max_price, price_offset, n_ranges: int = 4):
        self._max_price = max_price
        self._price_offset = price_offset
        self.n_ranges = n_ranges
        self.price_limits = []
        self.counters = []
        
        self._calculate_limits()
        self._reset_counters() 

    def _calculate_limits(self):
        self.price_limits = []        
        if self.n_ranges >= 1:
            for i in range(self.n_ranges+1):
                limit = self.min_price + (self.price_offset/self.n_ranges)*i
                self.price_limits.append(limit)
        
    def _reset_counters(self):
        self.counters = [0 for i in range(self.n_ranges)]
            
    @property
    def min_price(self):
        return self._max_price - self._price_offset

    @property
    def max_price(self):
        return self._max_price

    @max_price.setter
    def max_price(self, max_price):
        print(self)
        if max_price < self.min_price:
            self._reset_counters()
        self._max_price = max_price
        self._calculate_limits()
        print(self)

    @property
    def price_offset(self):
        return self._price_offset

    @price_offset.setter
    def price_offset(self, price_offset):
        self._price_offset = price_offset
        self._calculate_limits()

    @property
    def price_ranges(self):
        return [(self.price_limits[i], self.price_limits[i+1]) for i in range(len(self.price_limits)-1)]

    def increase_range_counter(self, index):
        if index:
            self.counters[index] += 1
    
    def decrease_range_counter(self, index):
        if index:
            print(self.counters)
            self.counters[index] = self.counters[index] - 1 if self.counters[index] > 0 else 0
            print(self.counters)
        
    def __str__(self):
        header = f'========= SAFETY ZONE =========\n'
        price_offset = f'Price Offset: {self._price_offset}\n'
        max_price = f'Max Price: {self.max_price}\n'
        min_price = f'Min Price: {self.min_price}\n'
        ranges = f'Ranges:\n{'\n'.join(map(str, self.price_ranges))}\n'
        counters = f'Counters: {self.counters}\n'

        return header + price_offset + max_price + min_price + ranges + counters