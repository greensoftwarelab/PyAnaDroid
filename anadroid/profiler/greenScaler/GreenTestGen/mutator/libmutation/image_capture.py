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


import os, subprocess, time, threading
import utils

def _makedir():
	subprocess.call(["adb", "shell", "rm -rf", "/sdcard/screen_shots"])	
	time.sleep(3)
	subprocess.call(["adb", "shell", "mkdir", "/sdcard/screen_shots"])

def _push_script(package):
	subprocess.call(["adb", "push", utils.BEST_EMU_PATH+package+".sh", "/sdcard/"])

def _run_screencap(package):
	subprocess.call("adb shell sh /sdcard/screen_capture.sh "+ package, shell=True)

def _load_app(package):
	subprocess.call("adb shell monkey -p " + package + " -c android.intent.category.LAUNCHER 1", shell=True)    
	time.sleep(10)

def _run_script(package):
	subprocess.call("adb shell sh /sdcard/"+package+".sh", shell=True)


def _pull_images(package):
	os.system("rm -rf "+utils.IMAGE_PATH+package)
	os.system("mkdir "+utils.IMAGE_PATH+package)
	subprocess.call("adb pull /sdcard/screen_shots/ "+utils.IMAGE_PATH+package, shell=True)

def _delete_images(package):

	subprocess.call(["adb", "shell", "rm", "-rf", "/sdcard/screen_shots"])
	time.sleep(3)
	subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/"+package+".sh"])

def capture_images(package):


	t1 = threading.Thread(target=_makedir)	
        t2 = threading.Thread(target=_push_script, args=(package,))
	t3 = threading.Thread(target=_run_screencap, args=(package,))
	t4 = threading.Thread(target=_load_app, args=(package,))
	t5 = threading.Thread(target=_run_script, args=(package,))
	t6 = threading.Thread(target=_pull_images, args=(package,))
	t7 = threading.Thread(target=_delete_images, args=(package,))
	print "making directory to /sdcard/"	
	t1.start()
        t1.join()
	print "pushing script"
	t2.start()
        t2.join()
	print "screencap started"
	t3.start()
	time.sleep(3)	
        #t3.join()
	print "loading app"
	t4.start()
        t4.join()
	print "running test"
	t5.start()
        t5.join()

	print "uninstall app"
	utils.uninstall_app(package)
	
	print "pulling images"
	t6.start()
        t6.join()

	print "deleting from phone"
	t7.start()
	t7.join()
