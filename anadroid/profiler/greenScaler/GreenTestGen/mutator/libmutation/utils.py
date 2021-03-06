"""
Copyright 2016 Shaiful Chowdhury, Stephanie Gil (shaiful@ualberta.ca, sgil@ualberta.ca)

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

import os, subprocess, time, threading

### this is the path to the GreenTestGen folder

#BASE_PATH = os.path.dirname(os.path.abspath(__file__))
BASE_PATH="/home/shaiful/research/shaiful_random_test_energy/final_data_upload_for_ICSE/Tools/GreenTestGen/"

SCRIPTS_PATH=BASE_PATH+"mutator/scripts"

## save all generated tests
TESTS_PATH=BASE_PATH+"mutator/dest/tests"
#### Tests will be generated for these apks. 
APKS_PATH=BASE_PATH+"mutator/source/apk_source/"
#### 
PROBLAMATIC_APKS=BASE_PATH+"mutator/dest/problematic_apks/"
##### this should be changed based on settings. 
AAPT_PATH="/home/shaiful/android/android-sdk-linux/build-tools/23.0.1/"
######### selected best tests for greenminer
BEST_TEST_PATH=BASE_PATH+"mutator/dest/best_tests_device/"
##########selected best tests for emulator################
BEST_EMU_PATH=BASE_PATH+"mutator/dest/best_tests_emu/"
########### duration for running on GreenMiner
DURATION_PATH=BASE_PATH+"mutator/dest/duration/"
##### This is needed to run generated tests on GreenMiner
APK_TO_PACKAGE=BASE_PATH+"mutator/dest/apk_to_package/"
#############
TRACK_PATH=BASE_PATH+"mutator/"
IMAGE_PATH=BASE_PATH+"mutator/dest/images/"
COUNTER=1
# python mutator.py test.sh 300 com.android2.calculator3 Calculator-debug-00083-65cbad5.apk 852 

def uninstall_app(pkg):
    if pkg is None:
        return
    subprocess.call("adb shell pm uninstall " + pkg, shell=True)

def install_app(apk):
    if apk is None:
        return
    subprocess.call("adb install " + apk, shell=True)

def clean_up(pkg_name, apk):
    """
        Removes any output files from previous run, uninstalls and reinstalls
        the app, finds the pid of the running app and returns it.
    """
    print("\n=================================================\n")
    print("Cleaning...\n")
    #subprocess.call("adb shell ps | grep " + pkg_name \
    #    + " | awk '{print $2}' | xargs adb shell kill", shell=True)
    #time.sleep(5)

    t1 = threading.Thread(target=uninstall_app,
                          args=(pkg_name,))
    t2 = threading.Thread(target=install_app,
                          args=(apk,))
    # uninstall app
    t1.start()
    t1.join()
    time.sleep(10)	
    if os.path.isfile("result.txt"):
        os.remove("result.txt")
    if os.path.isfile("run_methods.txt"):
        os.remove("run_methods.txt")
    if os.path.isfile("output.trace"):
        os.remove("output.trace")

    # install app again
    t2.start()
    t2.join()
    time.sleep(10)	
    # find pid again
    subprocess.call("adb shell monkey -p " + pkg_name + " -c android.intent.category.LAUNCHER 1", shell=True)
    time.sleep(10)
    while 1:
        try:
            bits = subprocess.check_output('adb shell ps | grep "' + pkg_name + '"', shell=True)
            print("\nDone cleaning.")
            break
        except:
            pass
    return bits.split()[1]	
