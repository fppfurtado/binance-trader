import decimal
from Position import Position

class Trade:

    def __init__(self, open_position: Position, close_position: Position):
        self.client = client
        self._open_position = open_position
        self._close_position = close_position

    @property
    def open_position(self):
        return self._open_position

    @open_position.setter
    def open_position(self, position: Position):
        self._open_position = position

    @property
    def close_position(self):
        return self._close_position

    @close_position.setter
    def close_position(self, position: Position):
        self._close_position = position