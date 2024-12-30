import os, time
from dotenv import load_dotenv
from binance.client import Client
from binance.ws.streams import ThreadedWebsocketManager
import analysis
from market_data import BinanceClient, BinanceWebsocket

def __main():
    load_dotenv(dotenv_path='../.env', override=True)
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')

    symbol = 'BTCUSDT'
    client = BinanceClient(API_KEY, API_SECRET)
    socket_manager = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)

    candles_monitor = BinanceWebsocket(symbol, socket_manager)
    candles_monitor.start()

    while True:
        support = analysis.get_support_price(client.get_historical_data(symbol, Client.KLINE_INTERVAL_1MINUTE),7)
        print(support)
        time.sleep(1)

if __name__ == '__main__':
    __main()