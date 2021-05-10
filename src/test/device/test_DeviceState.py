import time
from unittest import TestCase

from src.device.Device import get_first_connected_device


class TestDeviceState(TestCase):
    device = get_first_connected_device()

    def test_screen_lock(self):
        self.__class__.device.unlock_screen()
        res = self.__class__.device.device_state.get_screen_lock_state()
        self.assertTrue(res == 0)
        time.sleep(1)
        self.__class__.device.lock_screen()
        res = self.__class__.device.device_state.get_screen_lock_state()
        self.assertTrue(res == 1)


    def test_screen_brightness(self):
        self.__class__.device.device_state.set_screen_brightness(255)
        res = self.__class__.device.device_state.get_screen_brightness()
        self.assertTrue(res == 255)


    def test_screen_always_on(self):
        self.__class__.device.device_state.set_screen_always_on_while_plugged(1)
        res = self.__class__.device.device_state.get_screen_always_on()
        self.assertTrue(res == 1)
        self.__class__.device.device_state.set_screen_always_on_while_plugged(0)
        res = self.__class__.device.device_state.get_screen_always_on()
        self.assertTrue(res == 0)

    def test_screen_auto_rotate(self):
        self.__class__.device.device_state.set_screen_auto_rotate(1)
        res = self.__class__.device.device_state.get_screen_auto_rotate()
        self.__class__.device.device_state.set_screen_auto_rotate(0)
        res1 = self.__class__.device.device_state.get_screen_auto_rotate()
        self.assertTrue(res == 1 and res1 == 0)

    def test_screen_orientation(self):
        inval = 2
        last_val = 0
        self.__class__.device.device_state.set_screen_orientation(inval)
        res = self.__class__.device.device_state.get_screen_orientation()
        time.sleep(1)
        self.__class__.device.device_state.set_screen_orientation(last_val)
        res1 = self.__class__.device.device_state.get_screen_orientation()
        self.assertTrue(res == inval and res1 == last_val)


    def test_bluetooth_state(self):
        inval = 1
        last_val = 0
        self.__class__.device.device_state.set_bluetooth_state(inval)
        time.sleep(5)
        res = self.__class__.device.device_state.get_bluetooth_state()
        self.__class__.device.device_state.set_bluetooth_state(last_val)
        time.sleep(5)
        res1 = self.__class__.device.device_state.get_bluetooth_state()
        self.assertTrue(res == inval)# and res1==last_val)

    def test_wifi_state(self):
        inval = 1
        last_val = 0
        self.__class__.device.device_state.set_wifi_state(inval)
        time.sleep(5)
        res = self.__class__.device.device_state.get_wifi_state()
        self.__class__.device.device_state.set_wifi_state(last_val)
        time.sleep(5)
        res1 = self.__class__.device.device_state.get_wifi_state()
        self.assertTrue(res == inval and res1 == last_val)

    def test_gps_state(self):
        inval = 1
        last_val = 0
        self.__class__.device.device_state.set_gps_state(inval)
        time.sleep(5)
        res = self.__class__.device.device_state.get_gps_state()
        self.__class__.device.device_state.set_gps_state(last_val)
        time.sleep(5)
        res1 = self.__class__.device.device_state.get_gps_state()
        self.assertTrue(res == inval and res1 == last_val)

    def test_nfc_state(self):
        inval = 1
        last_val = 0
        self.__class__.device.device_state.set_nfc_state(inval)
        time.sleep(5)
        res = self.__class__.device.device_state.get_nfc_state()
        self.__class__.device.device_state.set_nfc_state(last_val)
        time.sleep(5)
        res1 = self.__class__.device.device_state.get_nfc_state()
        self.assertTrue(res == inval and res1 == last_val)

    def test_mobile_data_state(self):
        self.assertTrue(True)

    def test_speakers_state(self):
        input_val = 0
        self.__class__.device.device_state.change_speaker_state(input_val)
        res = self.__class__.device.device_state.get_speakers_state()
        self.assertTrue(res == input_val)