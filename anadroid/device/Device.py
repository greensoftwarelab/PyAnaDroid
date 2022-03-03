import json
import os
import re
from enum import Enum

from manafa.utils.Logger import log, LogSeverity

from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.device.AbstractDevice import AbstractDevice, ADB_CONN
import difflib

from anadroid.device.DeviceState import DeviceState, DEVICE_STATE_ENFORCE
from anadroid.utils.Utils import execute_shell_command, get_resources_dir

CONFIG_DIR = os.path.join(get_resources_dir(), 'config')
CONFIG_TEST_FILE = os.path.join(CONFIG_DIR, "device_state_on_test.json")
CONFIG_IDLE_FILE = os.path.join(CONFIG_DIR, "device_state_on_idle.json")
TCP_PORT = 5555


# assuming only 1 device connected
def set_device_conn(conn_type, device_id=None):
    """sets connection of type conn_type with a connected device or a device with id == device_id.
    Args:
        conn_type(ADB_CONN): connection type.
        device_id: device id.

    """
    device_string = f"-s {device_id}" if device_id is not None else ""
    if conn_type == ADB_CONN.USB or conn_type == ADB_CONN.USB.value:
        result = execute_shell_command(f'adb {device_string} disconnect; adb {device_string} usb')
        if result.validate("No devices/emulators found"):
            log("Device is now connected via USB")
    elif conn_type == ADB_CONN.WIFI or conn_type == ADB_CONN.WIFI.value:
        device = get_first_connected_device()
        if device.conn_type == ADB_CONN.WIFI:
            log("device already connected via wifi")
        else:
            res = execute_shell_command(f"adb {device_string} shell ip -f inet addr show wlan0")
            if "more than one device" in res.errors:
                log("more than one device connected. please specify device id or unplug the device", log_sev=LogSeverity.ERROR)
            elif res.validate("Error accessing device network interface") and res.output == "":
                log("no wifi connection detected on the device. Please connect the device to a wireless network", log_sev=LogSeverity.ERROR)
            else:
                reg = re.search(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', (res.output))
                if reg is None:
                    raise Exception("Bad address read")
                ip_addr = reg.group()
                res = execute_shell_command(f"adb {device_string} tcpip {TCP_PORT}; adb {device_string} connect {ip_addr}")
                if res.validate(f"error while connecting to {ip_addr} address") and f"connected to {ip_addr}" in res.output:
                    log(f"successfully connected to {ip_addr}", log_sev=LogSeverity.SUCCESS)

                log("Please unplug the device from the workstation in order to disable USB connection", log_sev=LogSeverity.WARNING)
    else:
        raise Exception("Unknown device connection type (not USB or WIFI)")


def get_first_connected_device(conn_type=ADB_CONN.USB.value):
    """Retrieves the first connected device that it founds using adb.
    Retrieves the first device of the list retrieved by adb devices -l command.
    Args:
        conn_type:

    Returns:
        Device: first device found.
    """
    result = execute_shell_command('adb devices -l  | grep \"product\"') # #| cut -f1 -d\ ')
    conn_type = ADB_CONN.USB if "usb" in result.output.lower() else ADB_CONN.WIFI
    result.validate(DeviceNotFoundError("No devices/emulators found"))
    device_serial = result.output.split(" ")[0]
    if device_serial == "":
        raise DeviceNotFoundError(f"No devices/emulators connected via {conn_type} found")

    return Device(device_serial, conn_type=conn_type)


class DeviceNotFoundError(Exception):
    pass


class Device(AbstractDevice):
    """Class that extends AbstractDevice to handle interaction with devices connected via ADB."""
    def __init__(self,  serial_nr, conn_type=ADB_CONN.USB):
        super(Device, self).__init__(serial_nr)
        self.conn_type = conn_type
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
        """returns props dict containing device properties that were obtained using getprop command.
        Returns:
            props(dict): dict with properties.
        """
        return self.props

    def execute_command(self, cmd, args=[], shell=False):
        return super().execute_command(cmd, args, shell)

    def execute_root_command(self, cmd, args=[], shell=False):
        return super(Device, self).execute_root_command(cmd, args, shell)

    def install_apks(self, andr_proj, build_type=BUILD_TYPE.RELEASE, install_test_apks=False):
        """install apks of type build_type of android project andr_proj.
        Args:
            andr_proj(AndroidProject):
            build_type(BUILD_TYPE): build type.
            install_test_apks(bool): if test apk installation has to be performed.

        Returns:
            installed_packages(set): set of installed packages.
        """
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
                log("package already installed")
                the_pack = self.get_package_matching(andr_proj.pkg_name)
                if the_pack is None:
                    continue
                else:
                    diff_pkgs = [the_pack]
            log("APK installed " + apk)
            self.installed_apks.append(apk)
            installed_pack = diff_pkgs[0]
            installed_packages.add(installed_pack)
            self.installed_packages.add(installed_pack)
        return installed_packages

    def install_apk(self, apk_path):
        """installs apk located in apk_path
        Args:
            apk_path(str): apk path.
        Returns:
            COMMAND_RESULT: result of installation command.
        """
        super(Device, self).execute_command("install -g -r ", args=[apk_path], shell=False)\
            .validate(Exception("Unable to install package " + apk_path))

    def unlock_screen(self, password=None):
       super(Device, self).unlock_screen(password)

    def is_screen_dreaming(self):
        return super(Device, self).is_screen_dreaming()

    def is_screen_unlocked(self):
        return super(Device, self).is_screen_unlocked()

    def uninstall_pkg(self, pkg_name):
        super().execute_command("uninstall ", args=[pkg_name], shell=False).validate(Exception("Unable to uninstall package " + pkg_name))

    def list_installed_packages(self):
        """returns list of device's installed packages.
        Returns:
            vals(:obj:`list` of :obj:`str`): list of packages.
        """
        vals = []
        res = super().execute_command("pm list packages", args=[], shell=True)
        res.validate( Exception("Error obtaining device packages"))
        for line in res.output.splitlines():
            val = re.sub(r'package:', '', line).strip()
            vals.append(val)
        return vals

    def get_min_sdk_version(self):
        """returns min sdk version of device.
        Gets ro.build.version.min_supported_target_sdk property.
        Returns:
            int: major min sdk version.
        """
        return int(self.props["ro.build.version.min_supported_target_sdk"]) if "ro.build.version.min_supported_target_sdk" in self.props else int(self.props["ro.build.version.sdk"])

    def get_device_sdk_version(self):
        """returns device sdk version.
        Gets ro.build.version.sdk.
        Returns:
            int: major min sdk version.
        """
        return int(self.props["ro.build.version.sdk"]) if "ro.build.version.sdk" in self.props else 19

    def __init_props(self):
        """fetch properties from device.
        Fills props attribute with properties coming from getprop command.
        """
        res = super().execute_command("getprop", args=[], shell=True)
        res.validate(DeviceNotFoundError("There is no connected devices"))
        for line in res.output.splitlines():
            vals= re.sub(r'\[|\]', '', line).split(":")
            if len(vals) > 1:
                self.props[vals[0]] = vals[1]

    def __init_installed_packages(self):
        """updates installed packages list.
        """
        packs = self.list_installed_packages()
        self.installed_packages.update(packs)

    def get_package_matching(self, pkg_aprox_name):
        """gets installed package more alike with a given pkg name.
        Args:
            pkg_aprox_name: name of the package.

        Returns:
            str: the most alike installed pkg name.
        """
        matching_list = list(filter(lambda x: pkg_aprox_name in x, self.installed_packages))
        if len(matching_list) > 0:
            return difflib.get_close_matches(pkg_aprox_name, matching_list)[0]
        else:
            # pkg_name diff after install
            return difflib.get_close_matches(pkg_aprox_name, self.installed_packages)[0]

    def lock_screen(self):
        super(Device, self).lock_screen()

    def has_package_installed(self, pack_name):
        """checks if a given package is installed on device.
        Args:
            pack_name: package name.

        Returns:
            bool: True if installed, False otherwise.
        """
        return pack_name in self.installed_packages

    def contains_file(self, filepath):
        """checks if device has a file in a given filepath.
        Args:
            filepath: path of file to check.

        Returns:
            bool: True if file exists, False otherwise.
        """
        res = self.execute_command("test -e ", args=[filepath], shell=True)
        return res.return_code == 0

    def clear_logcat(self):
        """clear device logs."""
        super().execute_command("logcat -c", args=[])\
            .validate()

    def dump_logcat_to_file(self, filename="logcat.out"):
        """dumps device logs to file with path filename.
        Args:
            filename: path or name of file.
        """
        super().execute_command(f"logcat -d > {filename}", args=[]) \
            .validate(Exception("Unable to dump logcat to file"))

    def get_device_android_version(self):
        return super().get_device_android_version()

    def is_rooted(self):
        """check if it is a rooted device.
        Returns:
            bool: True if is rooted, False otherwise.
        """
        return super().execute_command("su -c 'echo hi'", shell=True).validate()

    def load_device_state(self, filepath):
        """load device state from a file located in filepath
        Args:
            filepath: location of file with the state.

        Returns:
            json_def(dict): dict with state.
        """
        json_def={}
        with open(filepath, 'r') as filehandle:
            json_def = json.load(filehandle)
        return json_def

    def set_device_state(self, state_cfg=DEVICE_STATE_ENFORCE.TEST, perm_json=None):
        """enforces a given device state.
        Args:
            state_cfg(DEVICE_STATE_ENFORCE): type of state to enforce
            perm_json: set of states to enforce according to the permission to give in such state.
        """
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
        """if a new pkg was installed, retrieves a list of the new installed packages.
        Returns:
            new_pkgs(:obj:`list` of :obj:`str`): list of new packages.
        """
        old_pkgs = self.installed_packages
        new_pkgs = self.list_installed_packages()
        has_no_prefix = lambda candidate, pklist:  len(list(filter(lambda z: z in candidate and z != candidate, pklist))) == 0
        return list(filter(
            lambda x: x not in old_pkgs and has_no_prefix(x, new_pkgs),
            new_pkgs))

    def set_log_size(self, log_size_bytes=16384):
        """sets log size through persist.logd.size property.
        Args:
            log_size_bytes: size in bytes.
        """
        super(Device, self).execute_root_command(f"shell setprop persist.logd.size {log_size_bytes}K", shell=True)

