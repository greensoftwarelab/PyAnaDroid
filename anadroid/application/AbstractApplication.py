from abc import ABC, abstractmethod


class AbstractApplication(ABC):
    """Abstract base class representing a mobile application and defining an interface
    to interact with the application on the device.

    Attributes:
        package_name (str): The package name of the app.
        version (str): The version number of the app (default is '0.0').
        on_fg (bool): A flag indicating whether the app is in the foreground.
    """

    def __init__(self, package_name, version="0.0"):
        """Initializes an AbstractApplication instance.

        Args:
            package_name (str): The package name of the app.
            version (float, optional): The version number of the app (default is 0.0).
        """
        self.package_name = package_name
        self.version = version
        self.on_fg = False

    def get_app_id(self):
        """Get the unique app identifier.

        Returns:
            str: The app identifier in the format '<package_name>_<version>'.
        """
        return f'{self.package_name}_{self.version}'

    @abstractmethod
    def start(self):
        """Abstract method to start the application."""
        pass

    @abstractmethod
    def kill(self):
        """Abstract method to kill the application."""
        pass

    @abstractmethod
    def stop(self):
        """Abstract method to stop the application."""
        pass

    @abstractmethod
    def perform_action(self, act):
        """Abstract method to perform a specific action within the application.

        Args:
            act: The action to be performed within the application.
        """
        pass
