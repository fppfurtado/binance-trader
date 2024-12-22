import os
from APIClient import BinanceClient
from dotenv import load_dotenv

def __main():
    load_dotenv(dotenv_path='../.env')
    API_KEY = os.environ['BINANCE_API_KEY']
    API_SECRET = os.environ['BINANCE_API_SECRET']
    
    client = BinanceClient(API_KEY, API_SECRET)

    print(client.get_system_status())

if __name__ == '__main__':
    __main()