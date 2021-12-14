import json
import os
import re
from enum import Enum

from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.device.AbstractDevice import AbstractDevice, ADB_CONN
import difflib

from anadroid.device.DeviceState import DeviceState, DEVICE_STATE_ENFORCE
from anadroid.utils.Utils import execute_shell_command

CONFIG_DIR = os.path.join("resources", "config")
CONFIG_TEST_FILE = os.path.join(CONFIG_DIR, "device_state_on_test.json")
CONFIG_IDLE_FILE = os.path.join(CONFIG_DIR, "device_state_on_idle.json")


def get_first_connected_device(conn_type=ADB_CONN.USB):
    #TODO connect via wifi
    result = execute_shell_command('adb devices -l  | grep \"product\" | cut -f1 -d\ ')
    result.validate(DeviceNotFoundError("No devices/emulators found"))
    device_serial = result.output.split("\n")[0]
    if device_serial == "":
        raise DeviceNotFoundError("No devices/emulators found")
    return Device(device_serial)


class DeviceNotFoundError(Exception):
    pass

class Device(AbstractDevice):
    def __init__(self,  serial_nr):
        super(Device, self).__init__(serial_nr)
        self.props = {}
        self.state = None
        self.installed_packages = set()
        self.__init_installed_packages()
        self.__init_props()
        self.device_state = DeviceState(self)
        self.device_state_test = self.load_device_state(CONFIG_TEST_FILE)
        self.device_state_idle = self.load_device_state(CONFIG_IDLE_FILE)
        self.installed_apks = []

    def get_device_props(self):
        return self.props

    def execute_command(self, cmd, args=[], shell=False):
        return super().execute_command(cmd, args, shell)

    def execute_root_command(self, cmd, args=[]):
        return super(Device, self).execute_root_command(cmd,args)

    def install_apks(self, andr_proj, build_type=BUILD_TYPE.RELEASE, install_test_apks=False):
        apks_built = andr_proj.get_apks(build_type)
        if install_test_apks:
            apks_built += andr_proj.get_test_apks()
        installed_packages = set()
        for apk in apks_built:
            old_packs = self.installed_packages
            res = super().execute_command("install -r %s" % apk, args=[], shell=False)
            new_packs = self.list_installed_packages()
            diff_pkgs = list(filter(lambda x: x not in old_packs, new_packs))
            if len(diff_pkgs) == 0:
                print("package already installed")
                the_pack = self.get_package_matching(andr_proj.pkg_name)
                if the_pack is None:
                    continue
                else:
                    diff_pkgs = [the_pack]
            print("APK installed " + apk)
            self.installed_apks.append(apk)
            installed_pack = diff_pkgs[0]
            installed_packages.add(installed_pack)
            self.installed_packages.add(installed_pack)
        return installed_packages

    def install_apk(self, apk_path):
        pass

    def unlock_screen(self, password=None):
       super(Device, self).unlock_screen(password)

    def is_screen_dreaming(self):
        return super(Device, self).is_screen_dreaming()

    def is_screen_unlocked(self):
        return super(Device, self).is_screen_unlocked()

    def uninstall_pkg(self, pkg_name):
        super().execute_command("uninstall ", args=[pkg_name], shell=False).validate(Exception("Unable to uninstall package " + pkg_name))

    def list_installed_packages(self):
        vals = []
        res = super().execute_command("pm list packages", args=[], shell=True)
        res.validate( Exception("Error obtaining device packages"))
        for line in res.output.splitlines():
            val = re.sub(r'package:', '', line).strip()
            vals.append(val)
        return vals

    def get_min_sdk_version(self):
        return int(self.props["ro.build.version.min_supported_target_sdk"]) if "ro.build.version.min_supported_target_sdk" in self.props else int(self.props["ro.build.version.sdk"])

    def get_device_sdk_version(self):
        return int(self.props["ro.build.version.sdk"]) if "ro.build.version.sdk" in self.props else 19

    def __init_props(self):
        res = super().execute_command("getprop", args=[], shell=True)
        res.validate(DeviceNotFoundError("There is no connected devices"))
        for line in res.output.splitlines():
            vals= re.sub(r'\[|\]', '', line).split(":")
            if len(vals) > 1:
                self.props[vals[0]] = vals[1]

    def __init_installed_packages(self):
        packs = self.list_installed_packages()
        self.installed_packages.update(packs)

    def get_package_matching(self, pkg_aprox_name):
        matching_list = list(filter(lambda x: pkg_aprox_name in x, self.installed_packages))
        if len(matching_list) > 0:
            return difflib.get_close_matches(pkg_aprox_name, matching_list)[0]
        else:
            # pkg_name diff after install
            return difflib.get_close_matches(pkg_aprox_name, self.installed_packages)[0]

    def lock_screen(self):
        super(Device, self).lock_screen()

    def has_package_installed(self,pack_name):
        return pack_name in self.installed_packages

    def contains_file(self, filepath):
        res = self.execute_command("test -e ", args=[filepath],shell=True)
        return res.return_code == 0

    def clear_logcat(self):
        super().execute_command("logcat -c", args=[])\
            .validate()

    def dump_logcat_to_file(self, filename="logcat.out"):
        super().execute_command(f"logcat -d > {filename}", args=[]) \
            .validate(Exception("Unable to dump logcat to file"))

    def get_device_android_version(self):
        return super().get_device_android_version()

    def is_rooted(self):
        return super().execute_command("su -c 'echo hi'", shell=True).validate()

    def load_device_state(self, file):
        json_def={}
        with open(file, 'r') as filehandle:
            json_def = json.load(filehandle)
        return json_def

    def set_device_state(self, state_cfg=DEVICE_STATE_ENFORCE.TEST, perm_json=None):
        vals = {}
        if state_cfg == DEVICE_STATE_ENFORCE.APP and perm_json is not None:
            for perm in perm_json:
                vals += self.device_state.get_states_from_permission(perm)
        elif state_cfg == DEVICE_STATE_ENFORCE.TEST:
            vals = self.device_state_test
        elif state_cfg == DEVICE_STATE_ENFORCE.IDLE:
            vals = self.device_state_idle
        for k, v in vals.items():
            self.device_state.enforce_state(k, v)


    def get_new_installed_pkgs(self):
        old_pkgs = self.installed_packages
        new_pkgs = self.list_installed_packages()
        has_no_prefix = lambda candidate, pklist :  len(list(filter(lambda z: z in candidate and z != candidate, pklist))) == 0
        return list(filter(
            lambda x: x not in old_pkgs and has_no_prefix(x, new_pkgs),
            new_pkgs))

    def set_log_size(self, log_size_bytes=16384):
        super(Device, self).execute_root_command(f"shell setprop persist.logd.size {log_size_bytes}K", shell=True)

