


from abc import ABC, abstractmethod


class AbstractProfiler(ABC):
    """Defines a basic interface to be implemented by supported profilers.
    Provides a set of methods that allow to manage a profiling session lifecycle.
    Attributes:
        profiler(Profiler): profiler.
        device(Device): target device.
        pkg_name(str): profiler package name.
        device_dir(str): path of device directory where remote results can be stored.
        dependency(str): dependencies to insert in apps to be profiled.
        plugin(str): build plugins to insert in apps to be profiled.
    """
    def __init__(self, profiler, device, pkg_name, device_dir=None, dependency=None, plugin=None):
        super().__init__()
        self.device = device
        self.profiler = profiler
        self.pkg_name = pkg_name
        self.dependency = dependency
        self.device_dir = device_dir
        self.plugin=plugin

    @abstractmethod
    def init(self, **kwargs):
        """method to setup profiler."""
        pass

    @abstractmethod
    def start_profiling(self, tag=""):
        """method to start profiling session."""
        pass

    @abstractmethod
    def stop_profiling(self, tag=""):
        """method to stop profiling session."""
        pass

    @abstractmethod
    def update_state(self, tag="", desc=""):
        """log states/events during profiling session."""
        pass

    @abstractmethod
    def export_results(self, filename):
        """export profiling session results."""
        pass

    @abstractmethod
    def get_dependencies_location(self):
        """return location of dependencies."""
        pass

    @abstractmethod
    def needs_external_dependencies(self):
        """checks if external dependencies are needed."""
        return False
