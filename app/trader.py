import os, time
from APIClient import BinanceClient
from dotenv import load_dotenv
from binance.client import Client
from binance.ws.streams import ThreadedWebsocketManager
from Indicators import ExponentialMovingAverage
from history_manager import PriceHistoryManager


def __main():
    load_dotenv(dotenv_path='../.env')
    API_KEY = os.environ['BINANCE_API_KEY']
    API_SECRET = os.environ['BINANCE_API_SECRET']

    client = BinanceClient(API_KEY, API_SECRET)
    socket_manager = ThreadedWebsocketManager(api_key=API_KEY, api_secret=API_SECRET)

    price_manager = PriceHistoryManager(client, socket_manager, 100)
    price_manager.start()

    while True:
        ema = ExponentialMovingAverage.calculate(price_manager.get_closing_prices(), 7)
        print(ema)
        time.sleep(1)

if __name__ == '__main__':
    __main()