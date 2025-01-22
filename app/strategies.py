from backtrader import Strategy, Order, Sizer
import analysis as a
from datetime import datetime, timedelta
import numpy as np
import logging

class DefaultStrategy(Strategy):
    logger = logging.getLogger('trader')

    params = (
        ('stake', 10000),
        ('target_profit', 0.01),
        ('max_open_trades', 1),     # Limite máximo de operações abertas
        ('buy_price_limit_target_profit_percent', 1),
        ('buy_price_discount_target_profit_percent', 0.5),
        ('hours_to_expirate', 6)
    )

    def log(self, txt, dt=None, carriage_return=False):
        '''Logging function for the strategy'''
        dt = dt or self.datas[0].datetime.datetime()
        if not carriage_return:
            # print('%s, %s' % (dt, txt))
            self.logger.info('%s, %s' % (dt, txt))
        else:
            # print('\r%s, %s' % (dt, txt))
            self.logger.info('\r%s, %s' % (dt, txt))

    def __init__(self):
        self.data = self.datas[0]
        self.close = self.datas[0].close
        self.starting_price = self.datas[0].close[0]
        self.stake_per_order = self.p.stake / self.p.max_open_trades
        self.executed_buy_orders = []
        self.open_sell_orders = []
        self.executed_sell_orders = []
        self.total_profit = 0
        self.bar_executed = None
        self.max_price = -1
        self.min_price = -1
        
    def next(self):
        # rastreia preço máximo
        if self.data.high[0] > self.max_price:
            self.max_price = self.data.high[0]

        #rastreia preço mínimo
        if self.min_price < 0 or self.data.low[0] < self.min_price:
            self.min_price = self.data.low[0]

        # self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.open_sell_orders), self.close[0], self.data.high[0], self.data.low[0]))
        bar_current = len(self)
        current_price = self.close[0]

        if self.broker.cash > 0 and len(self.open_sell_orders) < self.p.max_open_trades and self.has_buy_signal():
            buy_price_limit = self.max_price * (1 - self.p.target_profit * self.p.buy_price_limit_target_profit_percent)
            buy_price = min(current_price * (1 - self.p.target_profit * self.p.buy_price_discount_target_profit_percent), buy_price_limit)
            order_expiration = timedelta(hours=self.p.hours_to_expirate)
            main_order = self.buy(exectype=Order.Limit, price=buy_price, size=self.stake_per_order/buy_price,transmit=False, valid=order_expiration)

            if main_order:
                position = main_order.price * main_order.size
                sell_price = (position + (self.stake_per_order * self.p.target_profit))/main_order.size
                take_profit_order = self.sell(parent=main_order, exectype=Order.Limit, price=sell_price, size=main_order.size, transmit=True, parent_price=main_order.price, range_index=None)
                        
                self.open_sell_orders.append(take_profit_order)                    
                
            self.bar_executed = len(self)

    def notify_order(self, order):
        #print(f'Ordem ref {order.ref}, Status {order.status}')
        if order.status == Order.Submitted:
            # pass
            self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.open_sell_orders), self.close[0], self.data.high[0], self.data.low[0]))            
            self.log('ORDER SUBMITTED(%s, %s, %s, %s) = %.2f' % (order.ref, order.ordtype, order.price, order.size, order.size * order.price)) 
        # if order.status == Order.Accepted:
        #     if order.isbuy():
        #         self.not_positioned_operations.append(order)
        if order.status in [Order.Completed]:
            self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.open_sell_orders), self.close[0], self.data.high[0], self.data.low[0]))            
            if order.isbuy():        
                self.log('BUY EXECUTED(%s, %s, %s) = %.2f' % (order.ref, order.executed.price, order.executed.size, order.executed.price*(order.executed.size)))
                self.executed_buy_orders.append(order)
            #elif order.issell():
            if order.issell():
                self.log('SELL EXECUTED(%s, %s, %s) = %.2f' % (str(order.parent.ref)+"."+str(order.ref), order.executed.price, order.executed.size, order.executed.price*(-order.executed.size)))
                self.open_sell_orders.remove(order)
                self.executed_sell_orders.append(order)
                self.total_profit = self.total_profit + (order.price - float(order.info['parent_price']))*(-order.size)
                
            # self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.open_sell_orders), self.close[0], self.data.high[0], self.data.low[0]))

            self.log(f'POSISION SIZE: {self.position.size}')
                
        if order.status == Order.Canceled:
                self.log('ORDER CANCELED(%s)' % (order.ref))
                if order.issell():
                    self.open_sell_orders.remove(order)

        if order.status == Order.Expired:
            self.log('ORDER EXPIRED(%s)' % (order.ref))
                
    def has_buy_signal(self) -> bool:
        if a.is_bullish(self._get_candle(0)):
            if a.is_bullish(self._get_candle(-1)):
                return True
    
    def _get_candle(self, index):
        return [
            self.data.datetime[index],
            self.data.open[index],
            self.data.high[index],
            self.data.low[index],
            self.data.close[index]
        ]