from enum import Enum

class OrderTime(Enum):
    GOOD_TIL_CANCELED = 'GTC'
    IMMEDIATE_OR_CANCEL = 'IOC'
    FILL_OR_KILL = 'FOK'
    GOOD_TIL_CROSS = 'GTX'
    