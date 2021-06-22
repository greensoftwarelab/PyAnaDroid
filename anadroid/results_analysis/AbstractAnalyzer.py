from abc import ABC, abstractmethod


class AbstractAnalyzer(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def setup(self, **kwargs):
        pass

    @abstractmethod
    def analyze(self, input_dir, test_orient, test_framework, output_log_file="AnaDroidAnalyzer.out"):
        pass

    @abstractmethod
    def clean(self):
        pass