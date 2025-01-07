import os, time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import analysis
from broker import BaseClient, BinanceClient
import backtrader as bt
from strategies import DefaultStrategy
import pandas as pd

asset_symbol: str = None
broker: BaseClient = None

def get_candles_by_date(year, month, day, interval = '1m'):
    date = datetime(year, month, day)
    
    start_time = datetime(date.year, date.month, date.day, 0, 0, 0)  # Start of the day (00:00:00)
    end_time = start_time + timedelta(days=1)  # End of the day (23:59:59)
    
    start_timestamp = int(start_time.timestamp()) * 1000
    end_timestamp = int(end_time.timestamp()) * 1000
    
    klines = broker.get_historical_data(asset_symbol, start_str=start_timestamp, end_str=end_timestamp)

    start_timestamp_2 = klines[-1][0] + 1

    klines.extend(broker.get_historical_data(asset_symbol, start_str=start_timestamp_2, end_str=end_timestamp))

    return klines

    
def candles_to_dataframe(candles):
    df = pd.DataFrame(
            candles, 
            columns=[
                'timestamp', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ]
        )
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def __init():
    load_dotenv(dotenv_path='../.env', override=True)
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    global asset_symbol
    asset_symbol = input('Informe o Ativo a ser operado: ').upper()

    global broker
    broker = BinanceClient(API_KEY, API_SECRET, asset_symbol)

def __main():

    __init()

    cerebro = bt.Cerebro()

    cerebro.addstrategy(DefaultStrategy, binance=broker)
    data_feed = bt.feeds.PandasData(dataname=candles_to_dataframe(get_candles_by_date(2025, 1, 6)))
    cerebro.adddata(data_feed)
    cerebro.broker.set_cash(10000.0)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    results = cerebro.run()
    strategy = results[0]

    # Resumo do desempenho
    print("==== Resumo do Desempenho ====")
    # print(f"Índice de Sharpe: {strategy.analyzers.sharpe.get_analysis()['sharperatio']}")
    # print(f"Máximo Drawdown: {strategy.analyzers.drawdown.get_analysis()['max']['drawdown']}%")

    # Acessar os resultados do TradeAnalyzer
    #trade_analysis = results[0].analyzers
    # print(trade_analysis)

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
    print(strategy.position)
    print('=====================')
        
    # while broker is not None:
    #     support = analysis.get_support_price(broker.get_historical_data(asset_symbol))
    #     print(support)
    #     time.sleep(1)

if __name__ == '__main__':
    __main()