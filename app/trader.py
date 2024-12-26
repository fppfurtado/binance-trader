import os, time
from api_client import BinanceClient
from dotenv import load_dotenv
from binance.client import Client
from binance.ws.streams import ThreadedWebsocketManager
from analysis import ExponentialMovingAverage
from monitoring import PriceMonitor


def __main():
    load_dotenv(dotenv_path='../.env')
    API_KEY = os.environ['BINANCE_API_KEY']
    API_SECRET = os.environ['BINANCE_API_SECRET']

    client = BinanceClient(API_KEY, API_SECRET)
    socket_manager = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)

    price_manager = PriceMonitor(client, socket_manager, 100)
    price_manager.start()

    while True:
        print(price_manager.get_candles())
        time.sleep(1)

if __name__ == '__main__':
    __main()