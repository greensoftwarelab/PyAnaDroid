from abc import ABC, abstractmethod


class AbstractWorkLoad(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def add_unit(self,wunit):
        pass

    @abstractmethod
    def consume(self):
        pass

    @abstractmethod
    def flush(self):
        pass