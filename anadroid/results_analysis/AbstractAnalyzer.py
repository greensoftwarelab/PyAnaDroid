import os
from abc import ABC, abstractmethod

from anadroid.device.DeviceState import get_known_state_keys, DeviceState
from anadroid.results_analysis.filters.Filters import Filters
from anadroid.utils.Utils import get_analyzers_filter_file

DEFAULT_CFG_ANALYZERS_FILE = get_analyzers_filter_file()


class AbstractAnalyzer(ABC):
    """Defines a basic interface to be implemented by programs aiming to analyze and produce results about the data
    collected during the profiling session and profiled apps.
    Attributes:
        profiler(Profiler): profiler.
        supported_filters(set): default set of filters to validate analyzed results.
        validation_filters(set): additional set of filters provided via config file to validate analyzed results.
    """
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
    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        """Analyze a set of tests of a given app.
        Args:
            app(App): app.
            results_dir: directory where to store results.
        """
        pass

    @abstractmethod
    def analyze_test(self, app, test_id, **kwargs):
        """Analyze test identified by test_id of a given app.
        Args:
            app(App): app.
            test_id: test uuid.
        """
        pass

    @abstractmethod
    def validate_test(self, app, arg1, **kwargs):
        """validate results of a certain test."""
        return True

    @abstractmethod
    def show_results(self, app_list):
        pass

    def get_supported_filters(self):
        """return set of supported filters."""
        return self.supported_filters

    def supports_filter(self, filter_name):
        """check if a given filter is supported.
        Args:
            filter_name: name of the filter.
        Returns:
            bool: True if supported, False otherwise.
        """
        return filter_name in self.supported_filters

    @abstractmethod
    def validate_filters(self):
        """validate supported filters."""
        return True

    @abstractmethod
    def clean(self):
        """clean previous results."""
        pass

    @abstractmethod
    def get_val_for_filter(self, filter_name, add_data=None):
        """get correspondent value of a given filter
        Args:
            filter_name: name of the filter.
        Returns:
            value: filter value.
        """
        if filter_name in get_known_state_keys():
            ds = DeviceState(self.profiler.device)
            return ds.get_state(filter_name)
        else:
            return None
