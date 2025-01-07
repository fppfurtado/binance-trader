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
        self.buy_orders = []  # Lista para armazenar ordens de compra
        # self.sell_orders = []  # Lista para armazenar ordens de venda
        self.orders = {}
 
    def next(self):

        self.log('Close, %.2f' % self.dataclose[0])

        if  len(self.orders) < self.p.max_orders:

            match self.get_market_trend():
                case MarketTrend.HIGH:
                    # current_price = float(self.binance.get_current_price(self.symbol)['price'])            
                    current_price = self.dataclose[0]            
                    buy_order = self.buy(
                        price=current_price,
                        exectype=Order.Limit,
                        size=self.get_buy_size()
                    )
                    self.log('BUY CREATE[%.0f](%.2f, %.2f), %.2f' % (buy_order.ref, buy_order.price, buy_order.size, self.dataclose[0]))                    
                    self.buy_orders.append(buy_order)
                case MarketTrend.LOW:
                    pass
                case MarketTrend.UNDEFINED:
                    pass

    def notify_order(self, order):
        # print(f"Notificação de Ordem: {order}")
        if order.isbuy():
            if order.status in [Order.Completed]:
                self.log('BUY EXECUTED[%.0f](%.2f, %.2f), %.2f' % (order.ref, order.executed.price, order.executed.size, order.executed.price))
                take_profit_order = self.sell(
                        exectype=Order.Limit,
                        price=order.executed.price + 10,
                        size=self.get_sell_size(),
                        # parent=order
                    )
                self.log('SELL CREATE[%.0f](%.2f, %.2f), %.2f' % (order.ref, take_profit_order.price, take_profit_order.size, self.dataclose[0]))
                self.orders.update({take_profit_order.ref: (order, take_profit_order)})
                self.log(f'OPEN ORDERS: {len(self.orders)}')
        elif order.issell():
            if order.status in [Order.Completed]:
                self.log('SELL EXECUTED[%.0f](%.2f, %.2f), %.2f' % (self.orders[order.ref][0].ref, order.executed.price, order.executed.size, order.executed.price))
                self.log(f'PORTFOLIO: {self.broker.getvalue()}')
                self.orders.pop(order.ref)

    def get_market_trend(self) -> MarketTrend:
        if a.is_bullish(self.get_candle(0)):
            if a.is_bullish(self.get_candle(-1)):
                return MarketTrend.HIGH
            else:
                return MarketTrend.UNDEFINED
        else:
            if a.is_bullish(self.get_candle(-1)):
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

    def get_buy_size(self):
        # Fração do capital disponível
        cash_available = self.broker.get_cash() / self.p.max_orders
        size = cash_available / self.data.close[0]  # Quantidade baseada no preço de fechamento
        return size

    def get_sell_size(self):
        # Retorna a quantidade equivalente ao preço da última ordem de compra + 10 unidades do preço
        last_buy_price = self.buy_orders[-1].price
        sell_price = last_buy_price + 10  # Adiciona 10 unidades do preço
        quantity = self.buy_orders[-1].size  # Calcula a quantidade equivalente
        return quantity