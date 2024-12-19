import os
from binance.client import Client
from dotenv import load_dotenv

def __setup_api_client():
    load_dotenv()
    API_KEY = os.environ['BINANCE_API_KEY']
    API_SECRET = os.environ['BINANCE_API_SECRET']
    return Client(API_KEY, API_SECRET)


def __main():
    
    api_client = __setup_api_client()
    print(api_client.get_server_time())

if __name__ == '__main__':
    __main()