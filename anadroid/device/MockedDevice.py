from anadroid.device.Device import Device
from anadroid.utils.Utils import COMMAND_RESULT

DEFAULT_SDK_VERSION = 28

class MockedDevice(Device):
    """Mocks a connected device.
    The main use case is to mock some devices with custom properties or when the framework is building apps without
    a connected device."""
    def __init__(self):
        super(Device, self).__init__("0000")
        self.props = {}
        self.installed_packages = set()
        self.__init_installed_packages()
        self.__init_props()

    def execute_command(self, cmd, args=[], shell=False):
        return COMMAND_RESULT(-1, "", "Mocked Device")

    def execute_root_command(self, cmd, args=[], shell=True):
        return COMMAND_RESULT(-1, "", "Mocked Device")
    
    def __init_installed_packages(self):
        pass

    def __init_props(self):
        self.props["ro.build.version.sdk"] = DEFAULT_SDK_VERSION
