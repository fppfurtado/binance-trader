import os, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import analysis
from broker import BaseClient, BinanceClient
import backtrader as bt
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
    cerebro.addstrategy(DefaultStrategy, target_profit=(0.75 / 100))

    start_datetime = datetime(2024, 11, 1)
    end_datetime = start_datetime + timedelta(hours=6)
    # end_datetime = start_datetime + timedelta(days=90)
    candles = broker.get_klines(asset_symbol, start_time=start_datetime, end_time=end_datetime, interval='1m')
    df_candles = broker.candles_to_dataframe(candles)
    
    data_feed = bt.feeds.PandasData(dataname=df_candles)
    cerebro.adddata(data_feed)

    stake = 10000
    cerebro.broker.set_cash(stake)

    # Run over everything
    results = cerebro.run()
    
    # Resumo do desempenho    
    print_results(cerebro, results)
    
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

def print_results(cerebro, results):
    strategy = results[0]

    print("====== PERFORMANCE REPORT ======")
    print(f'START PORTFOLIO VALUE: {strategy.p.stake}')
    print(f'CASH: {cerebro.broker.cash}')
    print(f'TARGET PROFIT: {strategy.p.target_profit * 100}%')
    print(f'POSITION SIZE: {strategy.position.size}')
    print(f'POSITION PRICE: {strategy.position.price}')
    print(f'BUYS EXECUTED: {len(strategy.executed_buy_orders)}')
    print(f'SELLS EXECUTED: {len(strategy.executed_sell_orders)}')
    print(f'TOTAL PROFIT: {strategy.total_profit} ({(strategy.total_profit/strategy.p.stake*100):.2f}%)')
    print(f'MAX PRICE: {strategy.max_price}')
    print(f'TOTAL TRADES: {int(cerebro.broker.get_orders_open()[-1].ref)/2}')
    print(f'FINAL PORTFOLIO VALUE: {cerebro.broker.getvalue()}')
    print('\n')
    print(f'******* OPEN ORDERS *******')
    print(f'{'\n------------------------\n'.join(map(str, cerebro.broker.get_orders_open()))}\n')
    print('=====================')

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