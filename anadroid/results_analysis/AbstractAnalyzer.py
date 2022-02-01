import os
from abc import ABC, abstractmethod

from anadroid.results_analysis.filters.Filters import Filters
from anadroid.utils.Utils import get_resources_dir
from manafa.utils.Logger import log

DEFAULT_CFG_ANALYZERS_FILE = os.path.join(get_resources_dir(), "config", "analyzer_filters.json")

class AbstractAnalyzer(ABC):
    def __init__(self, analyzers_cfg_file=DEFAULT_CFG_ANALYZERS_FILE):
        super().__init__()
        self.validation_filters = Filters(self.__class__.__name__, analyzers_cfg_file)
        self.supported_filters = set()

    @abstractmethod
    def setup(self, **kwargs):
        pass

    @abstractmethod
    def analyze_tests(self, app, results_dir=None, **kwargs):
        pass

    @abstractmethod
    def analyze_test(self, app, test_id, **kwargs):
        pass

    @abstractmethod
    def validate_test(self, app, arg1, **kwargs):
        pass

    @abstractmethod
    def show_results(self, app_list):
        pass

    def get_supported_filters(self):
        return self.supported_filters

    def supports_filter(self, filter_name):
        return filter_name in self.supported_filters

    @abstractmethod
    def validate_filters(self):
        return False

    @abstractmethod
    def clean(self):
        pass