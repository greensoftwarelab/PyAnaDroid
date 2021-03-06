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
import sys, os, time, datetime, subprocess, threading
from utils import *
class Test(object):
    """
        Represents a tapnswipe test. The script is the actual commands
        for an emulator (eg. input tap 23 23) and the coverage is
        the percentage of how many methods are called during the test.
    """

    def __init__(self, script="", coverage=0, app_pkg=""):
        self.script = script
        self.coverage = coverage
        self.app_pkg = app_pkg
        # http://stackoverflow.com/questions/13890935/timestamp-python
        now = datetime.datetime.fromtimestamp(time.time())
        self.timestamp = now.strftime('%Y-%m-%d_%H-%M-%S')
        self.name = self.app_pkg + "_" + self.timestamp + ".sh"
	self.duration=0 # modified by shaiful to capture test duration
    # http://jcalderone.livejournal.com/32837.html
    def __eq__(self, other):
        if isinstance(other, Test):
            return self.coverage == other.coverage
        return NotImplemented

    # http://jcalderone.livejournal.com/32837.html
    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __lt__(self, other):
        if isinstance(other, Test):
            return self.coverage < other.coverage
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Test):
            return self.coverage <= other.coverage
        return NotImplemented

    def __str__(self):
        return ("Name: %s; Coverage: %s")%(self.name, self.coverage)

    def set_name(self, name):
        self.name = name

    def set_script(self, script):
        self.script = script

    def set_coverage(self, coverage):
        """
            Sets the new coverage of the test. The physical test file will
            also be renamed to have the coverage appended to the front.
            Eg. If the test file is named "2014-05-25_4:25:01.sh", and if the
                coverage of the test has been calculated to be 85 %, it will
                be renamed to "85_2014-05-25_4:25:01.sh"
        """      
        self.coverage = coverage
        if os.path.isfile(TESTS_PATH + "/" + self.name):
            os.rename(TESTS_PATH + "/" + self.name, TESTS_PATH + "/" \
                      + self.app_pkg + "_"+self.timestamp + "_" \
                      + str(coverage) + ".sh")
        else:
            f_out = open(TESTS_PATH + "/" + self.app_pkg + "_"+self.timestamp \
                        + "_" + str(coverage) + ".sh", "w")
            f_out.write(self.script)
            f_out.close()
        self.name = self.app_pkg + "_" + self.timestamp + "_" + str(coverage) + ".sh" 

    def get_name(self):
        return self.name

    def get_script(self):
        return self.script
    	

    def get_coverage(self):
        return self.coverage

    def get_last_event(self):
        bits = self.script.split('\n')
        bits.remove('')
        if (len(bits) > 0):
            return bits[-1]
        return None

    def add_event(self, event):
        self.script += event

    def run(self,command=None):
        """
            Runs a test (script file) on a emulator.
        """
        f_out = open(TESTS_PATH + "/" + self.name,"w")
        f_out.write(self.script)
        f_out.close()

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
	print "start time="+str(st)
        t2.start()
        t2.join()
	en=time.time()
	print "end time="+str(en)
	print "duration="+str(en-st)
	self.duration=en-st
        print("\nDone running test.")
	t3.start()
	t3.join()
	return self.duration

    def delete(self):
        """
            Deletes the actualy script file the test represents. Test files
            should be in the tests/ subfolder of the current working dir.
        """
        if os.path.isfile(TESTS_PATH + "/" + self.name):
            os.remove(TESTS_PATH + "/" + self.name)

    def _push_test_on_phone(self):
	print "Now check to see if goes out of package, and modify accordingly"
        path = TESTS_PATH + "/" +  self.name

	fr=open(path,"r")
	lines=fr.readlines()
	fr.close()
	fw=open(path,"w")

	for line in lines:
		line=line.strip()
		fw.write(line+"\n")
		if "##" in line:
			continue ## it's a comment.. don't execute
		
		os.system("adb shell "+line)
		feed=commands.getstatusoutput('adb shell dumpsys window windows | grep -E \'mFocusedApp\'| cut -d / -f 1 | cut -d \" \" -f 7')
			#print feed[1]
		if feed[1]!=self.app_pkg:
			subprocess.call(["monkey -p" + self.app_pkg+"-c android.intent.category.LAUNCHER 1"])
			fw.write("monkey -p" + self.app_pkg+"-c android.intent.category.LAUNCHER 1\nsleep 4\n")					
			
			
			
	#fw=open(path,"a")
	fw.write("input keyevent HOME\nsleep 10")
	fw.close()	
        subprocess.call(["adb", "push", path, "/sdcard/"])
       
    def _run_test_on_phone(self):

        subprocess.call(["adb", "shell", "sh", "/sdcard/" \
                        + self.name])
    def _del_test_on_phone(self):
        subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        + self.name])	

