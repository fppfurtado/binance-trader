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
    
    klines = broker.get_klines(asset_symbol, start_str=start_timestamp, end_str=end_timestamp)

    start_timestamp_2 = klines[-1][0] + 1

    klines.extend(broker.get_klines(asset_symbol, start_str=start_timestamp_2, end_str=end_timestamp))

    return klines

    
def candles_to_dataframe(candles):
    df = pd.DataFrame(
            candles, 
            columns=[
                'datetime', 'open', 'high', 'low', 'close',
                'volume', 'close_time', 'quote_volume', 'trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ]
        )
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    # arr_date = df['datetime'].dt.to_pydatetime()
    # df['datetime'] = pd.Series(arr_date, dtype=object)
    # df['timestamp'] = datetime.utcfromtimestamp(df['timestamp'])
    # df.set_index('timestamp', inplace=True)

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

    cerebro.addstrategy(DefaultStrategy, binance=broker, target_profit=(0.05 / 100))

    start_datetime = datetime(2024, 12, 9)
    # end_datetime = start_datetime + timedelta(hours=1)
    end_datetime = start_datetime + timedelta(days=30)
    candles_10s = broker.get_10s_klines(asset_symbol, start_time=start_datetime, end_time=end_datetime)
    stake = 10000

    # ranges = candles_10s['high'] - candles_10s['low']
    # print(ranges)

    # print(candles_10s['close'].mean())
    # print(ranges.mean())

    # df_candles = candles_to_dataframe(get_candles_by_date(2025, 1, 6))
    # df_candles.set_index('datetime', inplace=True)
    # data_feed = bt.feeds.PandasData(dataname=df_candles)
    data_feed = bt.feeds.PandasData(dataname=candles_10s)
    cerebro.adddata(data_feed)
    cerebro.broker.set_cash(stake)

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    results = cerebro.run()
    strategy = results[0]

    # Resumo do desempenho
    print("==== Resumo do Desempenho ====")
    
    # Print out the final result
    print(f'Cash: {cerebro.broker.cash}')
    print(f'Position Size: {strategy.position.size}')
    print(f'Position Price: {strategy.position.price}')
    print(f'Buys Executed: {len(strategy.executed_buy_orders)}')
    print(f'Sells Executed: {len(strategy.executed_sell_orders)} ({(len(strategy.executed_sell_orders)/len(strategy.executed_buy_orders)*100):.2f}%)')
    print(f'Total Profit: {strategy.total_profit} ({(strategy.total_profit/stake*100):.2f}%)')
    print(f'Final Portfolio Value: {cerebro.broker.getvalue()}')
    print(f'High Trends: {strategy.trend_counters[0]}')
    print(f'Low Trends: {strategy.trend_counters[1]}')
    print(f'Undefined Trends: {strategy.trend_counters[2]}')
    print(f'Total Trends: {sum(strategy.trend_counters)}')
    print(strategy.fisrt_zone)
    print(strategy.safety_zone)
    # print(f' ---- Last Sell Order ----\n{strategy.pending_sell_orders[-1]}')
    # print(strategy.position)
    print('=====================')
    
    # while broker is not None:
    #     support = analysis.get_support_price(broker.get_historical_data(asset_symbol))
    #     print(support)
    #     time.sleep(1)

if __name__ == '__main__':
    __main()