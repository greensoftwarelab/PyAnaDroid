from abc import ABC, abstractmethod

DEFAULT_LOG_FILENAME="instrumentation_log.json"

class AbstractInstrumenter(ABC):
    def __init__(self):
        super().__init__()
        self.current_instr_type = None

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def instrument(self, **kwargs):
        pass

    @abstractmethod
    def needs_build_plugin(self):
        pass

    @abstractmethod
    def get_build_plugins(self):
       pass

    @abstractmethod
    def needs_build_dependency(self):
        pass

    @abstractmethod
    def get_build_dependencies(self):
        pass

    @abstractmethod
    def needs_build_classpaths(self):
        pass

    @abstractmethod
    def get_build_classpaths(self):
       pass

    @abstractmethod
    def get_log_filename(self):
        return DEFAULT_LOG_FILENAME
