from abc import ABC, abstractmethod


class AbstractAnalyzer(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def setup(self, **kwargs):
        pass

    @abstractmethod
    def analyze(self):
        pass

    @abstractmethod
    def clean(self):
        pass