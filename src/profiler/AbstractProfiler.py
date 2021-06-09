


from abc import ABC, abstractmethod


class AbstractProfiler(ABC):
    def __init__(self, profiler, device, pkg_name, device_dir=None, dependency=None, plugin= None):
        super().__init__()
        self.profiler = profiler
        self.device = device
        self.pkg_name = pkg_name
        self.dependency = dependency
        self.device_dir = device_dir
        self.plugin=plugin

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
    def get_dependencies_location(self):
        pass

    @abstractmethod
    def needs_external_dependencies(self):
        pass