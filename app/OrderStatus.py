from enum import Enum

class OrderStatus(Enum):
    NEW = 'NEW'
    FILLED = 'FILLED'
    CANCELLED = 'CANCELLED'