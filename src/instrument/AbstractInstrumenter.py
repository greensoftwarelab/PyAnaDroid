from abc import ABC, abstractmethod


class AbstractInstrumenter(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def instrument(self, **kwargs):
        pass