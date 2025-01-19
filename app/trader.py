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

def __main():

    __init()

    cerebro = bt.Cerebro()

    cerebro.addstrategy(DefaultStrategy, binance=broker, target_profit=(1 / 100))

    start_datetime = datetime(2024, 12, 9)
    # end_datetime = start_datetime + timedelta(hours=3)
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
    print(f'Max Price: {strategy.max_price}')
    print(f'Total Entries: {int(cerebro.broker.get_orders_open()[-1].ref)/2}')
    print(f'******* Open Orders *******\n{'\n------------------------\n'.join(map(str, cerebro.broker.get_orders_open()))}\n')
    # print(strategy.fisrt_zone)
    # print(strategy.safety_zone)
    # print(f' ---- Last Sell Order ----\n{strategy.pending_sell_orders[-1]}')
    # print(strategy.position)
    print('=====================')
    
    # while broker is not None:
    #     support = analysis.get_support_price(broker.get_historical_data(asset_symbol))
    #     print(support)
    #     time.sleep(1)
    
def __init():
    load_dotenv(dotenv_path='../.env', override=True)
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    global asset_symbol
    asset_symbol = input('Informe o Ativo a ser operado: ').upper()

    global broker
    broker = BinanceClient(API_KEY, API_SECRET, asset_symbol)

def get_price_difference_median(interval, period):
        # Obtendo os candles mensais dos últimos 24 meses (períodos de 1 mês)
        candles = self.binance.get_klines(symbol=self.symbol, interval=interval, limit=period)

        # Extrair os ranges (high - low) de cada candle
        ranges = [float(candle[2]) - float(candle[3]) for candle in candles]

        # Calcular a mediana
        return np.median(ranges)

if __name__ == '__main__':
    __main()