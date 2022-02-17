import os
from abc import ABC, abstractmethod

from anadroid.Config import get_general_config


class AbstractBuilder(ABC):
    def __init__(self, proj, device, resources_dir, instrumenter):
        super().__init__()
        self.android_home_dir = self.__get_android_home()
        self.proj = proj
        self.resources_dir = resources_dir
        self.instrumenter = instrumenter
        self.device = device
        self.__getDeviceInfo()
        self.config = get_general_config("build")

    def __get_android_home(self):
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
        return self.config[key] if key in self.config else default
