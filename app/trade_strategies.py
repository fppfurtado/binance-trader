from abc import ABC, abstractmethod

class TradeStrategy(ABC):
    @abstractmethod
    def execute():
        pass

