import re
import time
from enum import Enum

from anadroid.utils.Utils import loge


class DEVICE_STATE_ENFORCE(Enum):
    """Enumerates different states of device during benchmarking activity"""
    IDLE = "Idle"
    TEST = "Test conditions"
    APP = "App conditions"


KNOWN_STATE_KEYS = {
    "screen_locked",
    "screen_brightness",
    "screen_always_on",
    "screen_auto_rotate",
    "screen_orientation",
    "bluetooth",
    "wifi",
    # "hotspot_state",
    'gps',
    "nfc_state",
    "mobile_data_state",
    'speakers_state'
}

PERMISSIONS_TO_STATE = {
    "ACCESS_FINE_LOCATION": "gps_state",
    "BLUETOOTH": "bluetooth_state",
    "BLUETOOTH_ADMIN": "bluetooth_state",
    "BLUETOOTH_PRIVILEGED": "bluetooth_state",
    "INTERNET": "wifi",
    "NFC": "nfc_state",
    "NFC_TRANSACTION_EVENT": "nfc_state"
}


def get_known_state_keys():
    return KNOWN_STATE_KEYS


class DeviceState(object):
    """class that stores and represents the state of device components.

    Attributes:
        device(Device): device.
        screen_locked(int): 1 if screen locked, 0 otherwise.
        screen_brightness(int): screen brightness value (0-255).
        screen_always_on(int): if the screen should be always on.
        screen_auto_rotate(int): if the screen should rotate automatically.
        screen_orientation(int): screen orientation.
        bluetooth(int): state of bluetooth.
        wifi(int): wifi state.
        gps(int): gps state.
        nfc_state(int): nfc_state state.
        mobile_data_state(int): mobile_data_state state.
        speakers_state(int): speakers_state state.
        flashlight(int): flashlight state.
    """
    def __init__(self, device):
        self.device = device
        self.screen_locked = self.get_screen_lock_state()
        self.screen_brightness = self.get_screen_brightness()
        self.screen_always_on = self.get_screen_always_on()
        self.screen_auto_rotate = self.get_screen_auto_rotate()
        self.screen_orientation = self.get_screen_orientation()
        self.bluetooth = self.get_bluetooth_state()
        self.wifi = self.get_wifi_state()
        # self.hotspot_state = self.get_hotspot_state()
        self.gps = self.get_gps_state()
        self.nfc_state = self.get_nfc_state()
        self.mobile_data_state = self.get_mobile_data_state()
        self.speakers_state = self.get_speakers_state()
        self.flashlight = 0

    def get_screen_lock_state(self):
        """retrieve screen lock state.
        Returns:
            int: 0 if unlocked, 1 otherwise.
        """
        return 0 if self.device.is_screen_unlocked() else 1

    def get_screen_brightness(self):
        """retrieve screen brightness value.
        Returns:
            int: 0 - 255.
        """
        res = self.device.execute_command("settings get system screen_brightness", shell=True)
        if res.validate(("Unable to obtain screen brightness")):
            return int(re.search(r"[0-9]+", res.output).group())

    def get_screen_always_on(self):
        """retrieve screen always on state.
        gets value of stay_on_while_plugged_in setting.
        Returns:
           int: value.
        """
        res = self.device.execute_command("settings get global stay_on_while_plugged_in", shell=True)
        if res.validate(("Unable to obtain screen always_on val")):
            val = int(re.search(r"[0-9]+", res.output).group())
            return 0 if val == 0 else 1

    def get_screen_auto_rotate(self):
        """retrieve screen auto rotation state.
        gets value of system setting accelerometer_rotation.
        Returns:
           int: value.
        """
        res = self.device.execute_command("settings get system accelerometer_rotation", shell=True)
        if res.validate(("Unable to obtain screen auto rotate val")):
            return int(re.search(r"[0-9]+", res.output).group())

    def get_screen_orientation(self):
        """retrieve screen orientation state.
        gets value of system setting user_rotation.
        Returns:
           int: value.
        """
        res = self.device.execute_command("settings get system user_rotation", shell=True)
        if res.validate(Exception("Unable to obtain screen auto rotate val")):
            return int(re.search(r"[0-9]+", res.output).group())

    def get_bluetooth_state(self):
        """retrieve bluetooh state.
        Returns:
            int: 0 if off, 1 otherwise.
        """
        res = self.device.execute_command("settings get global bluetooth_on", shell=True)
        if res.validate(("Unable to obtain bluetooth state")):
            return int(re.search(r"[0-1]", res.output).group())

    def get_wifi_state(self):
        """retrieve wifi state.
        Returns:
            int: 0 if off, 1 otherwise.
        """
        res = self.device.execute_command("settings get global wifi_on", shell=True)
        if res.validate(("Unable to obtain wifi state")):
            return int(re.search(r"[0-1]", res.output).group())

    def get_hotspot_state(self):
        """retrieve hotspot state.
        Returns:
            int: 0 if off, 1 otherwise.
        """
        res = self.device.execute_command("dumpsys wifi | grep \"curState=TetheredState\"  | grep -E \"[A-Za-z]\"",
                                          shell=True)
        res1 = self.device.execute_command("dumpsys wifi | grep \"curState=ApEnabledState\"  | grep -E \"[A-Za-z]\"",
                                           shell=True)
        if res.validate() and res1.validate():
            return 1 if (res.output != "" or res1.output != "") else 0
        return 0

    def get_gps_state(self):
        """retrieve gps state.
        Returns:
            int: 0 if off, 1 otherwise.
        """
        res = self.device.execute_command("settings get secure location_providers_allowed | grep \"gps\"", shell=True)
        if res.validate(("Unable to obtain gps state")):
            return 1 if "gps" in res.output else 0

    def get_nfc_state(self):
        """retrieve nfc state.
        Returns:
            int: 0 if off, 1 otherwise.
        """
        res = self.device.execute_command("dumpsys nfc | grep \"mState=on\"", shell=True)
        if res.validate("Unable to obtain nfc state"):
            return 1 if "on" in res.output else 0

    def get_mobile_data_state(self):
        """retrieve mobile data state.
        Returns:
            int: 0 if off, 1 otherwise.
        """
        res = self.device.execute_command("settings get global  device_provisioning_mobile_data", shell=True)
        if res.validate(("Unable to obtain mobile data state")):
            return 1 if "1" in res.output else 0

    def get_speakers_state(self):
        """retrieve speakers state.
        Returns:
            int: 0 if off, 1 otherwise.
        """
        # ring and notifications vol?
        res = self.device.execute_command("dumpsys audio | grep \"STREAM_SYSTEM:\" -A 1", shell=True)
        if res.validate(("unable to obtain speakers state ")):
            return 1 if "false" in res.output.lower() else 0

    # setters
    def set_screen_lock_state(self, state=0):
        """set screen lock state. if state = 0, unlocks screen. Otherwise, it locks the screen.
        Args:
            state: lock state.
        """
        if state == 0:
            # unlock
            self.device.unlock_screen()
        else:
            # lock
            self.device.lock_screen()
        self.screen_locked = state

    def set_screen_brightness(self, value=0):
        """sets brightness value.
        Args:
            value: value between 0-255.
        """
        res = self.device.execute_command(f"settings put system screen_brightness {value}", shell=True)
        res.validate(("unable to set brightness value of %d " % value))
        self.screen_brightness = value
        print("olaaa")

    def set_screen_always_on_while_plugged(self, value=0):
        """set screen always on state. if state = 1 set stay on value.
        Args:
            value: state value.
        """
        # adb shell settings put global stay_on_while_plugged_in 3
        if value == 1:
            # res = self.device.execute_command(f"settings put global stay_on_while_plugged_in 3", shell=True)
            res = self.device.execute_command(f"svc power stayon true", shell=True)
        else:
            res = self.device.execute_command(f"svc power stayon false", shell=True)
        res.validate(("unable to turn on/off screen always on "))
        self.screen_always_on = value

    def set_screen_auto_rotate(self, value=0):
        """set screen auto rotate state. if state = 1 set auto rotate value as 1 (enable).
        Args:
            value: state value.
        """
        if value == 1:
            res = self.device.execute_command(f" settings put system accelerometer_rotation 1", shell=True)
        else:
            # adb shell settings put system accelerometer_rotation 0  #disable auto-rotate
            res = self.device.execute_command(f" settings put system accelerometer_rotation 0", shell=True)
        res.validate(("unable to turn on/off screen autorotate"))
        self.screen_auto_rotate = value

    def set_screen_orientation(self, value=0):
        """set screen orientation state. if state = 1, sets landscape mode. Otherwise, sets
        orientation as portrait mode.
        Args:
            value: state value.
        """
        # adb shell settings put system user_rotation 0 -> portrait
        # adb shell settings put system user_rotation 1 -> landscape
        is_auto_rotating = self.screen_auto_rotate
        if is_auto_rotating == 1:
            self.set_screen_auto_rotate(0)
            time.sleep(2)
        res = self.device.execute_command(f"settings put system user_rotation {value}", shell=True)
        res.validate((f"unable to rotate screen to val {value}"))
        self.screen_orientation = value
        if is_auto_rotating == 1:
            self.set_screen_auto_rotate(1)

    def set_bluetooth_state(self, value=0):
        """set bluetooth state. if state = 1 enables bluetooth. Otherwise, disables it.
        Args:
            value: state value.
        """
        if self.device.is_rooted():
            if value == 1:
                # adb shell su -c "pm enable com.android.bluetooth"
                # adb shell su -c "service call bluetooth_manager 6"
                res = self.device.execute_root_command(f"pm enable com.android.bluetooth")
                res = self.device.execute_root_command(f"service call bluetooth_manager 6")
            else:
                res = self.device.execute_root_command(f"pm disable com.android.bluetooth")
            res.validate(("Unable to change bluetooth state"))
        else:
             loge("changing bluetooth state is only available for rooted devices")
        self.bluetooth = value

    def set_gps_state(self, value=0):
        """set gps state. if state = 1 enables gps. Otherwise, disables it.
        Args:
            value: state value.
        """
        if value == 1:
            # adb shell settings put secure location_providers_allowed -gps
            res = self.device.execute_root_command(f"settings put secure location_providers_allowed +gps")
        else:
            res = self.device.execute_root_command(f"settings put secure location_providers_allowed -gps")
        res.validate(("Unable to change gps state"))
        self.gps = value

    def set_nfc_state(self, value=0):
        """set nfc state. if state = 1 enables nft. Otherwise, disables it.
        Args:
            value: state value.
        """
        if value == 1:
            res = self.device.execute_root_command(f"svc nfc enable")
        else:
            res = self.device.execute_root_command(f"svc nfc disable")
        res.validate(("Unable to change nfc state"))
        self.nfc_state = value

    def change_speaker_state(self, value=0):
        """set speaker state. if state = 1 enables speakers. Otherwise, disables it.
        Args:
            value: state value.
        """
        if value != self.speakers_state:
            res = self.device.execute_command(f'input keyevent 164', shell=True)
            res.validate(("Unable to change speakers state"))
            self.speakers_state = 0 if value == 0 else 1

    def set_hotspot_state(self, value=0):
        raise NotImplemented()

    def set_mobile_data_state(self, value=0):
        """set mobile date state. if state = 1 enables mobile data. Otherwise, disables it.
        Args:
            value: state value.
        """
        if value == 1:
            res = self.device.execute_root_command(f"svc data enable")
        else:
            res = self.device.execute_root_command(f"svc data disable")
        res.validate(("Unable to change nfc state"))
        self.mobile_data_state = value

    def set_wifi_state(self, value=0):
        """set wifi state. if state = 1 enables wifi. Otherwise, disables it.
        Args:
            value: state value.
        """
        if value == 1:
            res = self.device.execute_root_command(f"svc wifi enable")
        else:
            res = self.device.execute_root_command(f"svc wifi disable")
        res.validate(("Unable to change wifi state"))
        self.wifi = value

    def get_states_from_permission(self, perm_id):
        """infers needed state changes from permission.
        Args:
            perm_id: permission key.
        """
        if perm_id in PERMISSIONS_TO_STATE:
            self.enforce_state(PERMISSIONS_TO_STATE[perm_id], 1)

    def get_state(self, key):
        """given a component uid/key, returns the current state of such component.
        Args:
            key: component uid/key.

        Returns:
            int: value.
        """
        if not key in KNOWN_STATE_KEYS:
            return None
        elif key == 'screen_locked':
            return self.get_screen_lock_state()
        elif key == 'screen_brightness':
            return self.get_screen_brightness()
        elif key == 'screen_always_on':
            return self.get_screen_always_on()
        elif key == 'screen_auto_rotate':
            return self.get_screen_auto_rotate()
        elif key == 'screen_orientation':
            return self.get_screen_orientation()
        elif key == 'bluetooth':
            return self.get_bluetooth_state()
        elif key == 'wifi':
            return self.get_wifi_state()
        elif key == 'gps':
            return self.get_gps_state()
        elif key == 'nfc_state':
            return self.get_nfc_state()
        elif key == 'mobile_data_state':
            return self.get_mobile_data_state()
        elif key == 'speakers_state':
            return self.get_speakers_state()
        # elif key == 'hotspot_state':
        #    self.set_hotspot_state(val)
        else:
            raise Exception(f"{key} not implemented")

    def enforce_state(self, key, val):
        """enforces a component state.
        Args:
            key: component uid/key.
            val: state value.
        """
        if not key in KNOWN_STATE_KEYS:
            return
        elif key == 'screen_locked':
            self.set_screen_lock_state(val)
        elif key == 'screen_brightness':
            self.set_screen_brightness(val)
        elif key == 'screen_always_on':
            self.set_screen_always_on_while_plugged(val)
        elif key == 'screen_auto_rotate':
            self.set_screen_auto_rotate(val)
        elif key == 'screen_orientation':
            self.set_screen_orientation(val)
        elif key == 'bluetooth':
            self.set_bluetooth_state(val)
        elif key == 'wifi':
            self.set_wifi_state(val)
        elif key == 'gps':
            self.set_gps_state(val)
        elif key == 'nfc_state':
            self.set_nfc_state(val)
        elif key == 'mobile_data_state':
            self.set_mobile_data_state(val)
        elif key == 'speakers_state':
            self.change_speaker_state(val)
        # elif key == 'hotspot_state':
        #    self.set_hotspot_state(val)
        else:
            raise Exception(f"{key} not implemented")
