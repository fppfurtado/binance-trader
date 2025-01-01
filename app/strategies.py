import backtrader as bt

class DefaultStrategy(bt.Strategy):
    def log(self, txt, dt=None):
        '''Logging function for the strategy'''
        dt = dt or self.datas[0].datetime.datetime()
        print('%s, %s' % (dt, txt))

    def __init__(self):
        self.dataclose = self.datas[0].close

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])
