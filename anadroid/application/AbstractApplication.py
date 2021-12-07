from abc import ABC, abstractmethod


class AbstractApplication(ABC):
    def __init__(self, package_name, version=0.0):
        self.package_name = package_name
        self.version = version
        self.on_fg = False
        super().__init__()

    @abstractmethod
    def start(self):
        self.on_fg = True
        pass

    @abstractmethod
    def kill(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def performAction(self, act):
        pass