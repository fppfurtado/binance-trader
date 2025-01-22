import os, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import analysis as a
from broker import BaseClient, BinanceClient
import backtrader as bt
import backtrader.analyzers as btanalyzers
from backtrader import TimeFrame
from strategies import DefaultStrategy
import pandas as pd
import logging.config
import json
import pathlib
import atexit

logger = logging.getLogger('trader')
asset_symbol: str = None
broker: BaseClient = None

def __main():

    __init()

    cerebro = bt.Cerebro()

    global broker
    # cerebro.addstrategy(DefaultStrategy, target_profit=(0.5 / 100))
    cerebro.optstrategy(
        DefaultStrategy,
        target_profit = [0.001, 0.0025, 0.005, 0.0075, 0.01, 0.02, 0.03],
        buy_price_limit_target_profit_percent = [0, 0.5, 1, 1.5],
        buy_price_discount_target_profit_percent = [0, 0.5, 1, 1.5],
        hours_to_expirate = [1, 2, 4, 6, 12]
    )

    start_datetime = datetime(2024, 10, 21)
    # end_datetime = start_datetime + timedelta(hours=6)
    end_datetime = start_datetime + timedelta(days=90)
    candles = broker.get_klines(asset_symbol, start_time=start_datetime, end_time=end_datetime, interval='1m')
    df_candles = broker.candles_to_dataframe(candles)
    
    data_feed = bt.feeds.PandasData(dataname=df_candles)
    cerebro.adddata(data_feed)

    stake = 10000
    cerebro.broker.set_cash(stake)

    # adicionando analyzers
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name = "sharpe", timeframe=TimeFrame.Days, riskfreerate=0.06)
    cerebro.addanalyzer(btanalyzers.DrawDown, _name = "drawdown")
    cerebro.addanalyzer(btanalyzers.Returns, _name = "returns", timeframe=TimeFrame.NoTimeFrame)
    cerebro.addanalyzer(a.ProfitReturns, _name = "profit")

    # Run over everything
    results = cerebro.run(exactbars=True)
    
    # Resumo do desempenho    
    print_opt_results(results)
    
def __init():

    setup_logging()

    global logger

    load_dotenv(dotenv_path='../.env', override=True)
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    global asset_symbol
    asset_symbol = input('Informe o Ativo a ser operado: ').upper()

    global broker
    broker = BinanceClient(API_KEY, API_SECRET, asset_symbol)

def print_opt_results(results):    
    par_list = [[x[0].params.target_profit, 
             x[0].params.buy_price_limit_enable,
             x[0].params.buy_price_limit_target_profit_percent,
             x[0].params.buy_price_discount_enable,
             x[0].params.buy_price_discount_target_profit_percent,
             x[0].params.hours_to_expirate,
             x[0].analyzers.profit.get_analysis()['total_profit'],
             x[0].analyzers.sharpe.get_analysis()['sharperatio'],
            #  x[0].analyzers.returns.get_analysis()['rtot'], 
             x[0].analyzers.drawdown.get_analysis()['max']['drawdown']             
            ] for x in results]
        	
    par_df = pd.DataFrame(par_list, columns = ['target_profit','bpl', 'bpl_perc', 'bpd', 'bpd_perc', 'hours_to_expirate','profit', 'sharpe','dd'])
    print(par_df.sort_values(by=['profit', 'sharpe'], ascending=False).head(10))

def setup_logging():
    config_file = pathlib.Path('logging.config.json')
    with open(config_file) as f_in:
        config = json.load(f_in)

    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)

if __name__ == '__main__':
    __main()