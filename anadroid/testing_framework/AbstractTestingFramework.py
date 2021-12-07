from abc import ABC, abstractmethod


class AbstractTestingFramework(ABC):
    def __init__(self, id, profiler):
        self.id = id
        self.profiler=profiler
        super().__init__()

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