import os, time
from dotenv import load_dotenv
import analysis
from broker import BaseClient, BinanceClient
import backtrader as bt
from strategies import DefaultStrategy

asset_symbol: str = None
broker: BaseClient = None

def buy():
    pass

def sell():
    pass

def __init():
    load_dotenv(dotenv_path='../.env', override=True)
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    global asset_symbol
    asset_symbol = input('Informe o Ativo a ser operado: ')

    global broker
    broker = BinanceClient(API_KEY, API_SECRET, asset_symbol)

def __main():

    __init()

    cerebro = bt.Cerebro()

    cerebro.addstrategy(DefaultStrategy)
    data_feed = bt.feeds.PandasData(dataname=broker.get_historical_data(asset_symbol))
    cerebro.adddata(data_feed)
    cerebro.broker.set_cash(10000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    
    # while broker is not None:
    #     support = analysis.get_support_price(broker.get_historical_data(asset_symbol))
    #     print(support)
    #     time.sleep(1)

if __name__ == '__main__':
    __main()