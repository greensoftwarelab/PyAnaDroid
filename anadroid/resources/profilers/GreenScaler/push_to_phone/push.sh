
"""
Copyright 2016 Shaiful Chowdhury (shaiful@ualberta.ca)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


adb push kill.sh /sdcard/kill.sh
adb push cpu_before.sh /sdcard/cpu_before.sh
adb push cpu_after.sh /sdcard/cpu_after.sh
adb push cpu_jiffy.sh /sdcard/cpu_jiffy.sh
adb push screen_capture.sh /sdcard/screen_capture.sh
adb push strc_gen.sh /sdcard/strc_gen.sh
adb push sysInfo_after.sh /sdcard/sysInfo_after.sh
adb push sysInfo_before.sh /sdcard/sysInfo_before.sh
