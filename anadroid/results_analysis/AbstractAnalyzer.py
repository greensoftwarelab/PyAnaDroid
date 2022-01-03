from abc import ABC, abstractmethod


class AbstractAnalyzer(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def setup(self, **kwargs):
        pass

    @abstractmethod
    def analyze(self, arg1, **kwargs):
        pass

    @abstractmethod
    def show_results(self, app_list):
        pass

    @abstractmethod
    def clean(self):
        pass