import re
import time
from enum import Enum


class DEVICE_STATE_ENFORCE(Enum):
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
    #"hotspot_state",
    'gps',
    "nfc_state",
    "mobile_data_state",
    'speakers_state'
}

PERMISSIONS_TO_STATE  = {
	"ACCESS_FINE_LOCATION" : "gps_state",
	"BLUETOOTH" : "bluetooth_state",
	"BLUETOOTH_ADMIN" : "bluetooth_state",
	"BLUETOOTH_PRIVILEGED" : "bluetooth_state",
	"INTERNET" : "wifi",
	"NFC" : "nfc_state",
	"NFC_TRANSACTION_EVENT" : "nfc_state"
}


class DeviceState(object):
    def __init__(self, device):
        self.device = device
        self.screen_locked = self.get_screen_lock_state()
        self.screen_brightness = self.get_screen_brightness()
        self.screen_always_on = self.get_screen_always_on()
        self.screen_auto_rotate = self.get_screen_auto_rotate()
        self.screen_orientation = self.get_screen_orientation()
        self.bluetooth = self.get_bluetooth_state()
        self.wifi = self.get_wifi_state()
        #self.hotspot_state = self.get_hotspot_state()
        self.gps = self.get_gps_state()
        self.nfc_state = self.get_nfc_state()
        self.mobile_data_state = self.get_mobile_data_state()
        self.speakers_state = self.get_speakers_state()
        self.flashlight = 0

    def get_screen_lock_state(self):
        return not self.device.is_screen_unlocked()

    def get_screen_brightness(self):
        res = self.device.execute_command("settings get system screen_brightness", shell=True)
        if res.validate(Exception("Unable to obtain screen brightness")):
            return int(re.search(r"[0-9]+", res.output).group())

    def get_screen_always_on(self):
        res = self.device.execute_command("settings get global stay_on_while_plugged_in", shell=True)
        if res.validate(Exception("Unable to obtain screen always_on val")):
            val = int(re.search(r"[0-9]+", res.output).group())
            return 0 if val == 0 else 1

    def get_screen_auto_rotate(self):
        res = self.device.execute_command("settings get system accelerometer_rotation", shell=True)
        if res.validate(Exception("Unable to obtain screen auto rotate val")):
            return int(re.search(r"[0-9]+", res.output).group())

    def get_screen_orientation(self):
        res = self.device.execute_command("settings get system user_rotation", shell=True)
        if res.validate(Exception("Unable to obtain screen auto rotate val")):
            return int(re.search(r"[0-9]+", res.output).group())

    def get_bluetooth_state(self):
        res = self.device.execute_command("settings get global bluetooth_on", shell=True)
        if res.validate(Exception("Unable to obtain bluetooth state")):
            return int(re.search(r"[0-1]", res.output).group())

    def get_wifi_state(self):
        res = self.device.execute_command("settings get global wifi_on", shell=True)
        if res.validate(Exception("Unable to obtain wifi state")):
            return int(re.search(r"[0-1]", res.output).group())

    def get_hotspot_state(self):
        res = self.device.execute_command("dumpsys wifi | grep \"curState=TetheredState\"  | grep -E \"[A-Za-z]\"",
                                          shell=True)
        res1 = self.device.execute_command("dumpsys wifi | grep \"curState=ApEnabledState\"  | grep -E \"[A-Za-z]\"",
                                           shell=True)
        if res.validate() and res1.validate():
            return res.output != "" or res1.output != ""

    def get_gps_state(self):
        res = self.device.execute_command("settings get secure location_providers_allowed | grep \"gps\"", shell=True)
        if res.validate(Exception("Unable to obtain gps state")):
            return 1 if "gps" in res.output else 0

    def get_nfc_state(self):
        res = self.device.execute_command("dumpsys nfc | grep \"mState=on\"", shell=True)
        if res.validate(Exception("Unable to obtain nfc state")):
            return  1 if "on" in res.output else 0

    def get_mobile_data_state(self):
        res = self.device.execute_command("settings get global  device_provisioning_mobile_data", shell=True)
        if res.validate(Exception("Unable to obtain mobile data state")):
            return 1 if "1" in res.output else 0

    def get_speakers_state(self):
        # ring and notifications vol?
        res = self.device.execute_command("dumpsys audio | grep \"STREAM_SYSTEM:\" -A 1", shell=True)
        if res.validate(Exception("unable to obtain speakers state ")):
            return 1 if "false" in res.output.lower() else 0

    # setters
    def set_screen_lock_state(self, state=0):
        if state == 0:
            # unlock
            self.device.unlock_screen()
        else:
            # lock
            self.device.lock_screen()
        self.screen_locked = state

    def set_screen_brightness(self, value=0):
        res = self.device.execute_command(f"settings put system screen_brightness {value}", shell=True)
        res.validate(Exception("unable to set brightness value of %d " % value))
        self.screen_brightness = value

    def set_screen_always_on_while_plugged(self, value=0):
        # adb shell settings put global stay_on_while_plugged_in 3
        if value == 1:
            # res = self.device.execute_command(f"settings put global stay_on_while_plugged_in 3", shell=True)
            res = self.device.execute_command(f"svc power stayon true", shell=True)
        else:
            res = self.device.execute_command(f"svc power stayon false", shell=True)
        res.validate(Exception("unable to turn on/off screen always on "))
        self.screen_always_on = value

    def set_screen_auto_rotate(self, value=0):
        if value == 1:
            res = self.device.execute_command(f" settings put system accelerometer_rotation 1", shell=True)
        else:
            # adb shell settings put system accelerometer_rotation 0  #disable auto-rotate
            res = self.device.execute_command(f" settings put system accelerometer_rotation 0", shell=True)
        res.validate(Exception("unable to turn on/off screen autorotate"))
        self.screen_auto_rotate = value

    def set_screen_orientation(self, value=0):
        # adb shell settings put system user_rotation 0 -> portrait
        # adb shell settings put system user_rotation 1 -> landscape
        is_auto_rotating = self.screen_auto_rotate
        if is_auto_rotating == 1:
            self.set_screen_auto_rotate(0)
            time.sleep(2)
        res = self.device.execute_command(f"settings put system user_rotation {value}", shell=True)
        res.validate(Exception(f"unable to rotate screen to val {value}"))
        self.screen_orientation = value
        if is_auto_rotating == 1:
            self.set_screen_auto_rotate(1)

    def set_bluetooth_state(self, value=0):
        if self.device.is_rooted():
            if value == 1:
                # adb shell su -c "pm enable com.android.bluetooth"
                # adb shell su -c "service call bluetooth_manager 6"
                res = self.device.execute_root_command(f"pm enable com.android.bluetooth")
                res = self.device.execute_root_command(f"service call bluetooth_manager 6")
            else:
                res = self.device.execute_root_command(f"pm disable com.android.bluetooth")
            res.validate(Exception("Unable to change bluetooth state"))
        else:
            raise Exception("changing bluetooth state is only available for rooted devices")
        self.bluetooth = value

    def set_gps_state(self, value=0):
        if value == 1:
            # adb shell settings put secure location_providers_allowed -gps
            res = self.device.execute_root_command(f"settings put secure location_providers_allowed +gps")
        else:
            res = self.device.execute_root_command(f"settings put secure location_providers_allowed -gps")
        res.validate(Exception("Unable to change gps state"))
        self.gps = value

    def set_nfc_state(self, value=0):
        if value == 1:
            res = self.device.execute_root_command(f"svc nfc enable")
        else:
            res = self.device.execute_root_command(f"svc nfc disable")
        res.validate(Exception("Unable to change nfc state"))
        self.nfc_state = value

    def change_speaker_state(self, value=0):
        if value != self.speakers_state:
            res = self.device.execute_command(f'input keyevent 164', shell=True)
            res.validate(Exception("Unable to change speakers state"))
            self.speakers_state = 0 if value == 0 else 1

    def set_hotspot_state(self, value=0):
        raise NotImplemented()
    def set_mobile_data_state(self, value=0):
        if value == 1:
            res = self.device.execute_root_command(f"svc data enable")
        else:
            res = self.device.execute_root_command(f"svc data disable")
        res.validate(Exception("Unable to change nfc state"))
        self.nfc_state = value

    def set_wifi_state(self, value=0):
        if value == 1:
            res = self.device.execute_root_command(f"svc wifi enable")
        else:
            res = self.device.execute_root_command(f"svc wifi disable")
        res.validate(Exception("Unable to change wifi state"))
        self.nfc_state = value

    def get_states_from_permission(self, perm_id):
        if perm_id in PERMISSIONS_TO_STATE:
            self.enforce_state(PERMISSIONS_TO_STATE[perm_id], 1)


    def enforce_state(self, key, val):
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
        #elif key == 'hotspot_state':
        #    self.set_hotspot_state(val)
        else:
            print(key)
            raise Exception("not implemented")