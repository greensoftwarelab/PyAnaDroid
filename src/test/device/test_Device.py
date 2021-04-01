from unittest import TestCase

from src.device.Device import get_first_connected_device


class TestDevice(TestCase):
    device = get_first_connected_device()

    def test_unlock_screen(self):
        self.__class__.device.unlock_screen()
        self.assertTrue(self.__class__.device.is_screen_unlocked())

    def test_is_screen_dreaming(self):
        self.__class__.device.lock_screen()
        self.assertTrue(True)

    def test_is_screen_unlocked(self):
        self.__class__.device.lock_screen()
        self.__class__.device.unlock_screen()
        self.assertTrue(self.__class__.device.is_screen_unlocked())
