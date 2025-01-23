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
    # global asset_symbol
    # cerebro.addstrategy(DefaultStrategy, target_profit=(0.5 / 100))
    cerebro.optstrategy(
        DefaultStrategy,
        target_profit = [0.0075, 0.01, 0.015, 0.025, 0.03],
        buy_price_limit_target_profit_percent = [0, 0.5, 1],
        buy_price_discount_target_profit_percent = [0, 0.5, 1],
        hours_to_expirate = [0.5, 1, 2, 4, 6, 12]
    )

    # start_datetime = datetime(2024, 10, 21)
    # end_datetime = start_datetime + timedelta(hours=2)
    # end_datetime = start_datetime + timedelta(days=90)
    # cerebro.addstrategy(
    #     DefaultStrategy, 
    #     target_profit=0.025, 
    #     # buy_price_limit_target_profit_percent=0.5, 
    #     # buy_price_discount_target_profit_percent=0.5, 
    #     hours_to_expirate=0.5
    # )
    
    # candles = get_candles(
    #     asset_symbol=asset_symbol,
    #     start_str='2024-10-21',
    #     time_offset_days=1,
    #     timeframe='1m',
    #     save_csv=True
    # )
    # df_candles = candles_to_dataframe(candles)
    df_candles = load_candles('data', asset_symbol)    
    
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
    results = cerebro.run()
    
    # Resumo do desempenho    
    # print_results(cerebro, results)
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

def get_candles(asset_symbol: str, start_str: str, end_str: str = None, time_offset_days:int = 0, timeframe: str = '1m', save_csv: bool = False):
    if end_str:
        period = daterange(start_str, end_str)
    else:
        period = daterange(start_str, time_offset_days=time_offset_days)

    for single_date in period:
        candles = broker.get_klines(asset_symbol, start_time=single_date, end_time=single_date + timedelta(hours=23, minutes=59), interval='1m')
        if save_csv:
            candles_to_dataframe(candles).to_csv(f'data/{asset_symbol}_{timeframe}_{single_date.strftime('%Y-%m-%d')}.csv', header=True, index=True)

    return candles

def load_candles(dir_name, asset_symbol):
    candles = []
    col_types = {
        'timestamp': 'str',
        'open': 'float64',
        'high': 'float64',
        'low': 'float64',
        'close': 'float64',
        'volume': 'float64',
        'close_time': 'str'
    }

    # Iterar sobre todos os arquivos na pasta 'data'
    for file_name in os.listdir(dir_name):
        # Verificar se o arquivo é um CSV
        if file_name.endswith('.csv'):
            
            # Carregar o arquivo CSV usando pandas
            file_path = os.path.join(dir_name, file_name)
            df = pd.read_csv(file_path, dtype=col_types)

            # Adicionar o DataFrame à lista de dados
            candles.append(df)

    # Concatenar todos os DataFrames na lista em um único DataFrame
    candles = pd.concat(candles)
    candles['timestamp'] = pd.to_datetime(candles['timestamp'])
    candles['close_time'] = pd.to_datetime(candles['close_time'])
    candles.set_index('timestamp', inplace=True)

    return candles
        
def daterange(start_str: str, end_str: str = None, time_offset_days: int = 0):

    start_date = datetime.strptime(start_str, '%Y-%m-%d')        

    if end_str:
        end_date = datetime.strptime(end_str, '%Y-%m-%d')
    else:
        end_date = start_date + timedelta(days=time_offset_days)

    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(days=n)
    # return (start_date, end_date)

def candles_to_dataframe(candles) -> pd.DataFrame:
    df = pd.DataFrame(
            candles, 
            columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time'
            ]
        )
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
    df.set_index('timestamp', inplace=True)

    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def print_opt_results(results):    
    par_list = [[x[0].params.target_profit, 
             x[0].params.buy_price_limit_target_profit_percent,
             x[0].params.buy_price_discount_target_profit_percent,
             x[0].params.hours_to_expirate,
             x[0].analyzers.profit.get_analysis()['total_profit'],
             x[0].analyzers.sharpe.get_analysis()['sharperatio'],
             x[0].analyzers.returns.get_analysis()['rtot'], 
             x[0].analyzers.drawdown.get_analysis()['max']['drawdown']             
            ] for x in results]
        	
    par_df = pd.DataFrame(par_list, columns = ['target_profit', 'bpl', 'bpd', 'hours_to_expirate','profit', 'sharp', 'return', 'dd'])
    print(par_df.sort_values(by=['profit', 'sharp', 'return'], ascending=False).head(20))

def print_results(cerebro, results):
    strategy = results[0]

    results = {}

    results.update({'general_header': '\n====== PERFORMANCE REPORT ======\n'})
    results.update({'start_portfolio_value': f'START PORTFOLIO VALUE: {strategy.p.stake:.2f}\n'})
    results.update({'cash': f'CASH: {cerebro.broker.cash:.2f}\n'})
    results.update({'target_profit': f'TARGET PROFIT: {strategy.p.target_profit * 100}%\n'})
    results.update({'position_size': f'POSITION SIZE: {strategy.position.size}\n'})
    results.update({'position_price': f'POSITION PRICE: {strategy.position.price:.2f}\n'})
    results.update({'buys_executed': f'BUYS EXECUTED: {strategy.executed_buy_orders_counter}\n'})
    results.update({'sells_executed': f'SELLS EXECUTED (TOTAL TRADES): {strategy.executed_sell_orders_counter}\n'})
    results.update({'starting_price': f'STARTING PRICE: {strategy.starting_price}\n'})    
    results.update({'min_price': f'MIN PRICE: {strategy.min_price:.2f} ({((strategy.min_price - strategy.starting_price)/strategy.starting_price*100):.2f}%)\n'})    
    results.update({'max_price': f'MAX PRICE: {strategy.max_price:.2f} ({((strategy.max_price - strategy.starting_price)/strategy.starting_price*100):.2f}%)\n'})
    results.update({'total_profit': f'TOTAL PROFIT: {strategy.total_profit:.2f} ({(strategy.total_profit/strategy.p.stake*100):.2f}%)\n'})
    results.update({'final_portfolio_value': f'FINAL PORTFOLIO VALUE: {cerebro.broker.getvalue():.2f}\n'})
    results.update({'orders_header': f'******* OPEN ORDERS *******\n'})
    results.update({'orders': f'{'\n------------------------\n'.join(map(str, cerebro.broker.get_orders_open()))}\n\n'})
    
    message = ''

    for key, value in results.items():
        message = message + value

    logger.info(message)

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