from abc import ABC, abstractmethod

from com.dtmilano.android.adb.adbclient import Device


class AbstractDevice(ABC):
    def __init__(self, serial_nr):
        self.inner_device = Device(serialno=serial_nr, status="device")
        super().__init__()

    def batata(self):
        pass