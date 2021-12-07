import re
from abc import ABC, abstractmethod
from enum import Enum

from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import execute_shell_command



class ADB_CONN(Enum):
    USB = "USB"
    WIFI = "WIFI"


class AbstractDevice(ABC):
    def __init__(self, serial_nr):
        self.serial_nr = serial_nr
        self.conn_type = ADB_CONN.USB # TODO
        super().__init__()

    @abstractmethod
    def execute_command(self, cmd, args=[], shell=False):
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
    def install_apks(self,apk_paths):
        pass

    @abstractmethod
    def uninstall_pkg(self, pkg_name):
        pass

    @abstractmethod
    def list_installed_packages(self,prop_name):
        pass

    @abstractmethod
    def unlock_screen(self, pwd=None):
        cmd = ""
        if self.is_screen_unlocked():
            print("screen already unlocked")
            return

        if self.is_screen_dreaming():
            # wake screen (pressing lock btn)
            cmd = "input keyevent 26;"
        if pwd is not None:
            # press lock btn -> swipe up -> passwd -> press enter
            print("password")
            self.execute_command(
                "\'{cmd}input touchscreen swipe 930 880 930 380 ; input text {pwd}; input input keyevent 66 \' ".format(
                    cmd=cmd,
                    pwd=pwd), args=[])
        else:
            # press lock button -> KEYCODE_MENU
            print("pra cima")
            res = self.execute_command("\'{cmd} input keyevent 82\'".format(cmd=cmd), args=[],shell=True)
            if not self.is_screen_unlocked():
                # if still locked -> swipe up
                res = self.execute_command("input touchscreen swipe 930 880 930 180 #", args=[],shell=True)
            res.validate()

    @abstractmethod
    def is_screen_unlocked(self):
        res = self.execute_command("dumpsys window | grep mDreamingLockscreen", args=[], shell=True)
        res.validate()
        is_locked = "true" in re.search("mDreamingLockscreen=(true|false|null)", res.output).groups()[0].lower()
        return not is_locked

    @abstractmethod
    def lock_screen(self):
        if not self.is_screen_unlocked():
            return
        res = self.execute_command("input keyevent 26", args=[], shell=True)

    @abstractmethod
    def is_screen_dreaming(self):
        res = self.execute_command("dumpsys window", args=[], shell=True)
        is_dreaming = "true" in re.search(" dreaming=(true|false|null)", res.output).groups()[0].lower() \
                      or "true" in re.search(" mDreamingLockscreen=(true|false|null)", res.output).groups()[0].lower()
        return is_dreaming

    @abstractmethod
    def get_device_android_version(self):
        res = self.execute_command("getprop ro.build.version.release", shell=True)
        if res.validate(Exception("Unable do get android device version")):
            return DefaultSemanticVersion(res.output.strip())