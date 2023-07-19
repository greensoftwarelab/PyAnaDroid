import time
from unittest import TestCase
from unittest.mock import Mock

from anadroid.device.Device import get_first_connected_device


class TestDevice(TestCase):
    device = get_first_connected_device()

    def test_unlock_screen(self):
        self.device.unlock_screen()
        self.assertTrue(self.device.is_screen_unlocked())

    def test_is_screen_unlocked(self):
        self.device.lock_screen()
        self.device.unlock_screen()
        self.assertTrue(self.device.is_screen_unlocked())

    def test_is_screen_dreaming(self):
        if self.device.is_screen_unlocked():
            self.device.lock_screen()
        time.sleep(2)
        self.device.press_lock_button()
        time.sleep(1)
        self.assertTrue(self.device.is_screen_dreaming())

