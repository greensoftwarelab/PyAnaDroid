from abc import ABC, abstractmethod

from anadroid.Config import get_general_config


class AbstractTestingFramework(ABC):
    """Defines a basic interface to be implemented by classes that provide integration of Android testing
    frameworks.
    Attributes:
        profiler(Profiler): profiler.
        id(str): testing framework uuid.
        analyzer(AbstractAnalyzer): Analyzer to be used.
        config(dict): set of testing frameowrk configurations.

    """
    def __init__(self, id, profiler, analyzer):
        super().__init__()
        self.id = id
        self.profiler = profiler
        self.analyzer = analyzer
        self.config = get_general_config("tests")

    @abstractmethod
    def init_default_workload(self, pkg, args_file=None, tests_dir=None):
        """initialize workload to be done by tests of the testing framework.
        Args:
            pkg: package of app under test.
            args_file: file containing test arguments, where each line contains arguments for 1 test.
            tests_dir: directory where test files or resources are stored.
        """
        pass

    def get_config(self, key, default=None):
        """get value of test configuration.
        Args:
            key: config name/key.
            default: default value to be returned in the case of missing configuration.
        """
        return self.config[key] if key in self.config else default

    @abstractmethod
    def execute_test(self, w_unit, timeout=None, *args, **kwargs):
        """execute a test described by a work unit w_unit.
        Args:
            w_unit(object): work unit containing information of the test to be executed.
            timeout: test timeout.
        """
        pass

    @abstractmethod
    def init(self):
        """initialize framework."""
        pass

    @abstractmethod
    def install(self):
        """install framework."""
        pass

    @abstractmethod
    def uninstall(self):
        """uninstall framework."""
        pass

    @abstractmethod
    def test_app(self, device, app):
        """test a given app on a given device."""
        pass

    def is_recordable(self):
        """checks if framework can record tests to be replayed."""
        return False

    def record_test(self, app_id=None, test_id=None, output_dir=None):
        """record test to be replayed later."""
        pass