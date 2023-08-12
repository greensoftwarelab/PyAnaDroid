import os
from abc import ABC, abstractmethod
from anadroid.Config import get_general_config


class AbstractBuilder(ABC):
    """
    An abstract class that defines the API for building apps using supported build systems.

    Attributes:
        android_home_dir (str): The path of the local Android home directory (value of $ANDROID_HOME).
        proj (`AndroidProject`): The project to build.
        device (`Device`): The targeted device.
        resources_dir (str): The pyanadroid resources directory.
        instrumenter (`AbstractInstrumenter`): The instrumentation tool used.
        config: Build configurations.

    """

    def __init__(self, proj, device, resources_dir, instrumenter):
        """
        Initializes a new instance of the AbstractBuilder class.

        Args:
            proj (`AndroidProject`): The project to build.
            device (`Device`): The targeted device.
            resources_dir (str): The pyanadroid resources directory.
            instrumenter (`AbstractInstrumenter`): The instrumentation tool used.

        """
        super().__init__()
        self.android_home_dir = self.__get_android_home()
        self.proj = proj
        self.resources_dir = resources_dir
        self.instrumenter = instrumenter
        self.device = device
        self.__get_device_info()
        self.config = get_general_config("build")

    @staticmethod
    def __get_android_home():
        """
        Gets the value of the environment variable ANDROID_HOME.

        Returns:
            android_home (str): Path to the Android SDK installation folder.

        Raises:
            Exception: If ANDROID_HOME is not set.

        """
        android_home = os.environ.get('ANDROID_HOME')
        if android_home is None or android_home == "":
            raise Exception("ANDROID_HOME not set")
        return android_home

    def __get_device_info(self):
        """
        Placeholder method for retrieving device information.
        Subclasses should implement this method to fetch device-related details.

        """
        pass

    @abstractmethod
    def build_apk(self):
        """
        Abstract method for building the main APK of the app.
        Subclasses must provide an implementation for building the APK.

        """
        pass

    @abstractmethod
    def build_tests_apk(self):
        """
        Abstract method for building the test APKs of the app.
        Subclasses must provide an implementation for building test APKs.

        """
        pass

    @abstractmethod
    def build(self):
        """
        Abstract method for the complete build process of the app.
        Subclasses must provide an implementation for the full build process.

        """
        pass

    def get_config(self, key, default=None):
        """
        Gets a configuration value identified by the given key.
        If no configuration is found, returns the specified default value.

        Args:
            key: The configuration key.
            default: The default value to return if the key is not found.

        Returns:
            value (str): The value of the configuration key, or the default value.

        """
        return self.config.get(key, default)
