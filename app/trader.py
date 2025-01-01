import os, time
from dotenv import load_dotenv
import analysis
from broker import BaseClient, BinanceClient

symbol: str = None
broker: BaseClient = None

def buy():
    pass

def sell():
    pass

def __init():
    load_dotenv(dotenv_path='../.env', override=True)
    API_KEY = os.getenv('BINANCE_API_KEY')
    API_SECRET = os.getenv('BINANCE_API_SECRET')
    
    global symbol
    symbol = input('Informe o Ativo a ser operado: ')

    global broker
    broker = BinanceClient(API_KEY, API_SECRET, symbol)

def __main():

    init()
    
    while True:
        support = analysis.get_support_price(broker.get_historical_data(symbol))
        print(support)
        time.sleep(1)

if __name__ == '__main__':
    __main()