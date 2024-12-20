class Trade:

    def __init__(self, client):
        self.client = client

    def get_quotation(self, symbol: str) -> str:
        return self.client.get_symbol_ticker(symbol=symbol)['price']

    def buy_market(self):
        pass

    def sell_limit(self):
        pass
