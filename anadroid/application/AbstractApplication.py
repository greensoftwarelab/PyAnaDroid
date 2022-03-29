from abc import ABC, abstractmethod


class AbstractApplication(ABC):
    """Main class that abstracts an app.

    Attributes:
        package_name: app package.
        version: app version.

    """
    def __init__(self, package_name, version=0.0):
        self.package_name = package_name
        self.version = version
        self.on_fg = False

    def get_app_id(self):
        return f'{self.package_name}_{self.version}'

    @abstractmethod
    def start(self):
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