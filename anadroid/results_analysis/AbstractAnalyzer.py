import os
from abc import ABC, abstractmethod

from anadroid.device.DeviceState import get_known_state_keys, DeviceState
from anadroid.results_analysis.filters.Filters import Filters
from anadroid.utils.Utils import get_resources_dir
from manafa.utils.Logger import log

DEFAULT_CFG_ANALYZERS_FILE = os.path.join(get_resources_dir(), "config", "analyzer_filters.json")

class AbstractAnalyzer(ABC):
    def __init__(self, profiler, analyzers_cfg_file=DEFAULT_CFG_ANALYZERS_FILE):
        super().__init__()
        self.profiler = profiler
        self.supported_filters = set() if not hasattr(self, 'supported_filters') else self.supported_filters
        self.supported_filters.update(get_known_state_keys())
        self.validation_filters = Filters(self.supported_filters, analyzers_cfg_file)

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
        return True

    @abstractmethod
    def show_results(self, app_list):
        pass

    def get_supported_filters(self):
        return self.supported_filters

    def supports_filter(self, filter_name):
        return filter_name in self.supported_filters

    @abstractmethod
    def validate_filters(self):
        return True

    @abstractmethod
    def clean(self):
        pass

    @abstractmethod
    def get_val_for_filter(self, filter_name):
        if filter_name in get_known_state_keys():
            ds = DeviceState(self.profiler.device)
            return ds.get_state(filter_name)
        else:
            return None
