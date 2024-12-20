class Position:

    BUY: str = 'BUY'
    SELL: str = 'SELL'
    
    def __init__(self, side: str, symbol: str, quantity: decimal, price: str):
        self._side = side
        self._symbol = symbol
        self._quantity = quantity
        self._price

    @property
    def side() -> str:
        return self._side

    @property
    def symbol() -> str:
        return self._symbol

    @property
    def quantity():
        return self._quantity

    @property
    def price():
        return self._price
    