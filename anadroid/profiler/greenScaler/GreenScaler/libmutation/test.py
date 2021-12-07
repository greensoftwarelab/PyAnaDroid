"""
Copyright 2016 Shaiful Chowdhury(shaiful@ualberta.ca)

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
import sys, os, time, datetime, subprocess, threading
import anadroid.profiler.greenScaler.GreenScaler.libmutation.utils
from anadroid.profiler.greenScaler.GreenScaler.libmutation.utils import *
import types

from anadroid.profiler.greenScaler.GreenTestGen.mutator.libmutation import utils


class Test(object):

    def __init__(self, apk, run=None):
        self.script = apk[:-4]+".sh"
        #self.app_pkg = app_pkg
        self.duration=0 # modified by shaiful to capture test duration
        if run:
            self._run = types.MethodType(run, self)

    def _run(self, command=None, args=[]):
        t1 = threading.Thread(target=self._push_test_on_phone)
        t2 = threading.Thread(target=self._run_test_on_phone)
        t3 = threading.Thread(target=self._del_test_on_phone)
        print("\n=================================================\n")
        print("Pushing test onto phone...")
        t1.start()
        t1.join()
        print("\nTest file now on phone.")

        print("\n=================================================\n")
        print("Running test...")
        st=time.time()
        print("start time="+str(st))
        t2.start()
        t2.join()
        en=time.time()
        print("end time="+str(en))
        print("duration="+str(en-st))
        self.duration=en-st
        print("\nDone running test.")
        t3.start()
        t3.join()
        return self.duration

    def run(self, command=None):
        st=time.time()
        print("start time="+str(st))
        print(command)
        self._run(command)
        en=time.time()
        print("end time="+str(en))
        print("duration="+str(en-st))
        self.duration=en-st
        return self.duration

    def _push_test_on_phone(self):

        subprocess.call(["adb", "push", utils.TESTS_PATH+self.script, "/sdcard/"])
       
    def _run_test_on_phone(self):
        subprocess.call(["adb", "shell", "sh", "/sdcard/" \
                        + self.script])
    def _del_test_on_phone(self):
        subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        + self.script]) 

