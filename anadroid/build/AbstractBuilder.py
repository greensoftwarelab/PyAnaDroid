import os
from abc import ABC, abstractmethod

from anadroid.Config import get_general_config


class AbstractBuilder(ABC):
    """Defines the API being used to build apps using supported build systems.
    Attributes:
        android_home_dir(str): path of local android home directory (value of $ANDROID_HOME).
        proj(`obj:`AndroidProject`): project to build.
        device(`obj:`Device`): targeted device.
        resources_dir(str): pyanadroid resources directory.
        instrumenter(`obj:`AbstracInstrumenter`): instrumentation tool used.
        config: build configurations.
    """
    def __init__(self, proj, device, resources_dir, instrumenter):
        super().__init__()
        self.android_home_dir = self.__get_android_home()
        self.proj = proj
        self.resources_dir = resources_dir
        self.instrumenter = instrumenter
        self.device = device
        self.__getDeviceInfo()
        self.config = get_general_config("build")

    @staticmethod
    def __get_android_home():
        """gets value of environment variable ANDROID_HOME.
        Returns:
            android_home(str): path to android sdk installation folder.
        """
        android_home = os.environ['ANDROID_HOME']
        if android_home is None or android_home == "":
            raise Exception("ANDROID_HOME not set")
        return android_home

    def __getDeviceInfo(self):
        pass

    @abstractmethod
    def build_apk(self):
        pass

    @abstractmethod
    def build_tests_apk(self):
        pass

    @abstractmethod
    def build(self):
        pass

    def get_config(self, key, default=None):
        """gets config value identified by key. if no configuration was found, returns default value.
        Args:
            key: configuration key.
            default: default value.

        Returns:
            value(str): value.
        """
        return self.config[key] if key in self.config else default
