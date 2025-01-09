from backtrader import Strategy, Order, Sizer
import analysis as a
from analysis import MarketTrend
from datetime import datetime

class DefaultStrategy(Strategy):
    params = (
        ('max_orders', 10),     # Limite máximo de ordens abertas
    )

    def log(self, txt, dt=None):
        '''Logging function for the strategy'''
        dt = dt or self.datas[0].datetime.datetime()
        print('%s, %s' % (dt, txt))

    def __init__(self, binance, symbol: str = 'BTCUSDT'):
        self.binance = binance
        self.symbol = symbol
        self.data = self.datas[0]
        self.dataclose = self.datas[0].close
        self.not_positioned_orders = {}  # Lista para armazenar ordens cuja compra não foi executada
        self.pending_sell_orders = []
        self.bar_executed = None
        # self.sell_orders = []  # Lista para armazenar ordens de venda
        #self.orders = {}
 
    def next(self):

        # self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))

        bar_current = len(self)

        if self.bar_executed and bar_current >= self.bar_executed + 30:
            if len(self.not_positioned_orders) > 0:
                for ref, order in self.not_positioned_orders.items():
                    # cashback = order[0].price*order[0].size
                    # self.log(f'CASHBACK: {cashback}')
                    # self.broker.add_cash(cashback)
                    self.broker.cancel(order[0])
                self.not_positioned_orders.clear()
                self.log('************** ALL NOT POSITIONED ORDERS CANCELED! ************** ')
            self.bar_executed = None
            
        #if  self.broker.cash > 0 and len(self.pending_sell_orders) < self.p.max_orders:
        if  self.broker.cash > 0 and len(self.pending_sell_orders) < self.p.max_orders:

            match self.get_market_trend():
                case MarketTrend.HIGH:
                    self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))
                    self.execute_high_trend_strategy()                 
                case MarketTrend.LOW:
                    pass
                case MarketTrend.UNDEFINED:
                    pass

    def execute_high_trend_strategy(self):
        # current_price = float(self.binance.get_current_price(self.symbol)['price'])
        current_price = self.dataclose[0]
        # discount = (0.05 / 100) * current_price
        # buy_price = current_price - discount
        buy_price = current_price
        main_order = self.buy(exectype=Order.Limit, price=buy_price, size=self.get_buy_size(self.p.max_orders),transmit=False)
        if main_order:
            #target_profit = (0.1 / 100) * main_order.price
            target_profit = (0.1 / 100)
            sell_price = main_order.price * (1 + target_profit)
            # sell_price = current_price - 0.01
            take_profit_order = self.sell(parent=main_order, exectype=Order.Limit, price=sell_price, size=main_order.size, transmit=True)
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
            #elif order.issell():
            if order.issell():
                self.log('SELL EXECUTED(%s, %s, %s) = %.2f' % (str(order.parent.ref)+"."+str(order.ref), order.executed.price, order.executed.size, order.executed.price*(-order.executed.size)))
                self.pending_sell_orders.remove(order)
            self.log('Cash %.2f, Open Sell Orders %s, Close %.2f, High %.2f, Low %.2f' % (self.broker.cash, len(self.pending_sell_orders), self.dataclose[0], self.data.high[0], self.data.low[0]))

            self.log(f'POSISION SIZE: {self.position.size}')
                
        if order.status == Order.Canceled:
                self.log('ORDER CANCELED(%s)' % (order.ref))
                if order.issell():
                    self.pending_sell_orders.remove(order)
                
                
    def get_market_trend(self) -> MarketTrend:
        if a.is_bullish(self.get_candle(-1)):
            if a.is_bullish(self.get_candle(-2)):
                return MarketTrend.HIGH
            else:
                return MarketTrend.UNDEFINED
        else:
            if a.is_bullish(self.get_candle(-2)):
                return MarketTrend.UNDEFINED
            else:
                return MarketTrend.LOW

    def get_candle(self, index):
        return [
            self.data.datetime[index],
            self.data.open[index],
            self.data.high[index],
            self.data.low[index],
            self.data.close[index]
        ]

    def get_buy_size(self, cash_divisor):
        # Fração do capital disponível
        cash_available = self.broker.get_cash() / cash_divisor
        size = cash_available / self.data.close[0]  # Quantidade baseada no preço de fechamento
        return size