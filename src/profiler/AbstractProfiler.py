


from abc import ABC, abstractmethod


class AbstractProfiler(ABC):
    def __init__(self, device, pkg_name, device_dir, dependency=None):
        super().__init__()
        self.device = device
        self.pkg_name = pkg_name
        self.dependency = dependency
        self.device_dir = device_dir

    @abstractmethod
    def init(self, **kwargs):
        pass

    @abstractmethod
    def start_profiling(self, tag=""):
        pass

    @abstractmethod
    def stop_profiling(self, tag=""):
        pass

    @abstractmethod
    def update_state(self, tag="", desc=""):
        pass

    @abstractmethod
    def export_results(self, filename):
        pass

    @abstractmethod
    def export_results(self, filename):
        pass

    @abstractmethod
    def get_dependency_location(self):
        pass