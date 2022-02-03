from abc import ABC, abstractmethod

from anadroid.Config import get_general_config


class AbstractTestingFramework(ABC):
    def __init__(self, id, profiler, analyzer):
        super().__init__()
        self.id = id
        self.profiler = profiler
        self.analyzer = analyzer
        self.config = get_general_config("tests")

    def get_config(self, key, default=None):
        return self.config[key] if key in self.config else default

    @abstractmethod
    def execute_test(self, w_unit, timeout=None, *args, **kwargs):
        pass

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def install(self):
        pass

    @abstractmethod
    def uninstall(self):
        pass

    @abstractmethod
    def test_app(self, device, app):
        pass

    def is_recordable(self):
        return False

    def record_test(self, app_id=None, test_id=None):
        pass