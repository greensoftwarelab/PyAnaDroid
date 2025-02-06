from abc import abstractmethod

from anadroid.analysis.AbstractAnalyzer import AbstractAnalyzer
from anadroid.utils.Utils import get_analyzers_filter_file

DEFAULT_CFG_ANALYZERS_FILE = get_analyzers_filter_file()


class ExecutionResultsAnalyzer(AbstractAnalyzer):
    """Defines a basic interface to be implemented by programs aiming to analyze and produce results about the data
    collected during the profiling session and profiled apps.
    Attributes:
        profiler(Profiler): profiler.
        supported_filters(set): default set of filters to validate analyzed results.
        validation_filters(set): additional set of filters provided via config file to validate analyzed results.
    """
    def __init__(self, profiler, analyzers_cfg_file=DEFAULT_CFG_ANALYZERS_FILE):
        super().__init__(analyzers_cfg_file)
        self.profiler = profiler


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
    def analyze_app(self, app, **kwargs):
        pass
