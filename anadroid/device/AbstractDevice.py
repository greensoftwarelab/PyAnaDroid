import re
from abc import ABC, abstractmethod
from enum import Enum


from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import execute_shell_command, logi


class ADB_CONN(Enum):
    """Class to enumerate different connectivity alternatives using ADB."""
    USB = "USB"
    WIFI = "WIFI"


class AbstractDevice(ABC):
    """Provides basic interface and functionality to interact with devices.

    Attributes:
        serial_nr(str): device serial number / uuid.
        conn_type(ADB_CONN): type of connection.
    """
    def __init__(self, serial_nr):
        self.serial_nr = serial_nr
        self.conn_type = ADB_CONN.USB
        super().__init__()

    @abstractmethod
    def execute_command(self, cmd, args=[], shell=False):
        """execute remote shell command with args on device.
        Returns:
            res(COMMAND_RESULT): result of command.
        """
        cmd = cmd + " " + ' '.join(args)
        res = execute_shell_command(
            "adb -s {serial} {shell} {command} ".format(
                        serial=self.serial_nr,
                        shell="" if not shell else "shell",
                        command=cmd
            )
        )
        return res

    @abstractmethod
    def execute_root_command(self, cmd, args=[], shell=True):
        """execute remote shell command with args on device in superuser mode.
        Returns:
            res(COMMAND_RESULT): result of command.
        """
        cmd = cmd + " " + ' '.join(args)
        ret = execute_shell_command(
            "adb -s {serial} {shell} su -c '{command}' ".format(
                serial=self.serial_nr,
                shell="" if not shell else "shell",
                command=cmd,
            )
        )
        return ret

    @abstractmethod
    def install_apks(self, apk_paths):
        pass

    @abstractmethod
    def uninstall_pkg(self, pkg_name):
        pass

    @abstractmethod
    def list_installed_packages(self):
        pass

    @abstractmethod
    def unlock_screen(self, pwd=None):
        """unlock device screen.
        Tries several approaches to unlock screen. It starts by trying to press lock button, followed by trying
        to type a password if a password is required. If none of these worked, tries to press menu button and finally,
        it tries to perform a swipe up.
        Args:
            pwd: password to provide if devices requires password to be unlocked.
        """
        cmd = "input keyevent 26;"  # lock button
        if self.is_screen_unlocked():
            logi("screen is unlocked")
            return

        if self.is_screen_dreaming():
            # wake screen (pressing lock btn)
            logi("screen is dreaming")
            execute_shell_command("adb shell input tap 300 300", args=[])
            cmd = ''
        if pwd is not None:
            # press lock btn -> swipe up -> passwd -> press enter
            print("Inserting password")
            self.execute_command(
                "\'{cmd}input touchscreen swipe 930 880 930 380 ; input text {pwd}; input input keyevent 66 \' ".format(
                    cmd=cmd,
                    pwd=pwd), args=[])
        else:
            # press lock button -> KEYCODE_MENU
            res = self.execute_command("\'{cmd} input keyevent 82\'".format(cmd=cmd), args=[], shell=True)
            if not self.is_screen_unlocked():
                # if still locked -> swipe up
                res = self.execute_command("input touchscreen swipe 930 880 930 180 #", args=[], shell=True)
            res.validate()

    def touch_screen(self, x_coord=500, y_coord=500):
        res = self.execute_command(f"input touchscreen tap {x_coord} {y_coord}", args=[], shell=True)
        res.validate()

    def press_lock_button(self):
        res = self.execute_command(" input keyevent 26", args=[], shell=True)
        res.validate()

    @abstractmethod
    def is_screen_unlocked(self):
        """Checks if screen is unlocked.
        Returns:
            bool: True if unlocked, False otherwise.
        """
        res = self.execute_command("dumpsys window | grep mDreamingLockscreen", args=[], shell=True)
        res.validate()
        is_locked = "true" in re.search("mDreamingLockscreen=(true|false|null)",
                                        res.output).groups()[0].lower() \
            if len(re.search("mDreamingLockscreen=(true|false|null)",
                             res.output).groups()) > 0 else False
        return not is_locked

    @abstractmethod
    def lock_screen(self):
        """Checks if screen is locked.
        Returns:
            bool: True if locked, False otherwise.
        """
        if not self.is_screen_unlocked():
            return
        self.execute_command("input keyevent 26", args=[], shell=True)

    @abstractmethod
    def is_screen_dreaming(self):
        """Checks if screen is dreaming.
        Returns:
            bool: True if dreaming, False otherwise.
        """
        res = self.execute_command("dumpsys power", args=[], shell=True)
        is_dreaming = 'true' in \
                      re.search("mHoldingDisplaySuspendBlocker=(true|false|null)", res.output).groups()[0].lower()
        return is_dreaming


    def reboot(self):
        self.execute_command('reboot', shell=False)

    @abstractmethod
    def get_device_android_version(self):
        """returns device android version.
        Retrieves value of ro.build.version.release property.
        Returns:
            DefaultSemanticVersion: android version.
        """
        res = self.execute_command("getprop ro.build.version.release", shell=True)
        if res.validate(Exception("Unable do get android device version")):
            return DefaultSemanticVersion(res.output.strip())
