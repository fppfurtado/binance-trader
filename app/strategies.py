from backtrader import Strategy, Order, Sizer, num2date
import analysis as a
from datetime import datetime, timedelta
import numpy as np
import logging
import backtrader as bt

class DefaultStrategy(Strategy):
    logger = logging.getLogger('trader')

    params = (
        ('stake', 10000),
        ('target_profit', 0.01),
        ('buy_price_limit_target_profit_percent', 0),
        ('buy_price_discount_target_profit_percent', 0),
        ('hours_to_expire', 6)
    )

    def log(self, txt, dt=None, carriage_return=False):
        '''Logging function for the strategy'''
        dt = dt or self.datas[0].datetime.datetime()
        if not carriage_return:
            # print('%s, %s' % (dt, txt))
            self.logger.debug('%s, %s' % (dt, txt))
        else:
            # print('\r%s, %s' % (dt, txt))
            self.logger.debug('\r%s, %s' % (dt, txt))

    def __init__(self):
        self.data = self.datas[0]
        self.close = self.datas[0].close
        self.starting_price = None
        self.open_buy_order = None
        self.executed_buy_orders_counter = 0
        self.executed_sell_orders_counter = 0
        self.total_profit = 0
        self.max_price = -1
        self.min_price = -1
        self.last_trade_date = None

        # bt.indicators.ExponentialMovingAverage()

    def next(self):
        # preço inicial do dataset
        if len(self) == 1:
            self.starting_price = self.close[0]

        # rastreia preço máximo
        if self.data.high[0] > self.max_price:
            self.max_price = self.data.high[0]

        #rastreia preço mínimo
        if self.min_price < 0 or self.data.low[0] < self.min_price:
            self.min_price = self.data.low[0]

        if self.open_buy_order:
            return

        # self.log('Cash %.2f, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, self.close[0], self.data.high[0], self.data.low[0]))
        if not self.position and self.has_buy_signal():
            current_price = self.close[0]
            
            buy_price_limit = self.max_price * (1 - self.p.target_profit * self.p.buy_price_limit_target_profit_percent)
            buy_price = min(current_price * (1 - self.p.target_profit * self.p.buy_price_discount_target_profit_percent), buy_price_limit)
            buy_size = self.broker.cash/buy_price if buy_price > 0 else current_price
            order_value = buy_price * buy_size

            if order_value <= self.broker.cash:
                order_expiration = timedelta(hours=self.p.hours_to_expire)
                main_order = self.buy(exectype=Order.Limit, price=buy_price, size=buy_size,transmit=False, valid=order_expiration)
                self.open_buy_order = main_order

                if main_order:
                    position = main_order.price * main_order.size
                    sell_price = (position + (self.broker.cash * self.p.target_profit))/main_order.size
                    self.sell(parent=main_order, exectype=Order.Limit, price=sell_price, size=main_order.size, transmit=True, parent_price=main_order.price)

                self.last_trade_date = num2date(self.data.datetime[0]).date()
                        
    def notify_order(self, order):
        #print(f'Ordem ref {order.ref}, Status {order.status}')
        match order.status:
            case Order.Submitted:
                # pass
                self.log('Cash %.2f, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, self.close[0], self.data.high[0], self.data.low[0]))            
                self.log('ORDER SUBMITTED(%s, %s, %s, %s) = %.2f' % (order.ref, order.ordtype, order.price, order.size, order.size * order.price)) 
        # if order.status == Order.Accepted:
        #     if order.isbuy():
        #         self.not_positioned_operations.append(order)
            case Order.Completed:
                self.log('Cash %.2f, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, self.close[0], self.data.high[0], self.data.low[0]))            
                if order.isbuy():        
                    self.log('BUY EXECUTED(%s, %s, %s) = %.2f' % (order.ref, order.executed.price, order.executed.size, order.executed.price*(order.executed.size)))
                    self.executed_buy_orders_counter += 1
                    self.open_buy_order = None
                #elif order.issell():
                if order.issell():
                    self.log('SELL EXECUTED(%s, %s, %s) = %.2f' % (str(order.parent.ref)+"."+str(order.ref), order.executed.price, order.executed.size, order.executed.price*(-order.executed.size)))
                    self.executed_sell_orders_counter += 1
                    self.total_profit = self.total_profit + (order.price - float(order.info['parent_price']))*(-order.size)
                    
                # self.log('Cash %.2f, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, self.close[0], self.data.high[0], self.data.low[0]))

                self.log(f'POSISION SIZE: {self.position.size}')
                
            case Order.Canceled:
                self.log('ORDER CANCELED(%s)' % (order.ref))
                    
            case Order.Expired:
                self.log('ORDER EXPIRED(%s)' % (order.ref))
                self.open_buy_order = None

            case Order.Margin:
                self.log('ORDER MARGIN(%s)' % (order.ref))

            case Order.Rejected:
                self.log('ORDER REJECTED(%s)' % (order.ref))

    def stop(self):
        self.logger.info(f'Finalizando DefaultStrategy(stake = {self.p.stake}, target_profit = {self.p.target_profit}, bpl = {self.p.buy_price_limit_target_profit_percent}, bpd = {self.p.buy_price_discount_target_profit_percent}, hours_to_expire = {self.p.hours_to_expire}): ({self.last_trade_date}, {self.total_profit:.2f})')
        
                
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