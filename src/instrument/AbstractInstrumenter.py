from abc import ABC, abstractmethod


class AbstractInstrumenter(ABC):
    def __init__(self):
        super().__init__()

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