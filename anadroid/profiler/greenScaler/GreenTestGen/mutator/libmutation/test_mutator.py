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

import commands
import time, os, subprocess, threading
from test import *
from events import *
from initial import Initial
import re
import utils
from random import randint

EVENTS=[Tap for i in range(12)]
EVENTS.extend([TapMenu for i in range(2)])
EVENTS.extend([Swipe for i in range(3)])
EVENTS.extend([Text for i in range(3)])
EVENTS.extend([KeyEvent for i in range(3)])
#EVENTS.extend([LongPress for i in range(2)]) ##only with real device


class TestMutator(object):
    
    def __init__(self, test, pid, pkg_name, apk=None):
        """
            Needs app name, test object, and pid of app on device.
            Eg. "calculator", calcTestObj, 1033
        """
        self.test = test
        self.pid = pid
        #self.num_methods = int(num_methods)
        self.pkg_name = pkg_name
        self.apk = apk
        self.repeat = 0 # Number of times mutated tests get the same coverage
        self.prev_test = Test("",0, self.pkg_name)  # last test that had a higher coverage
        self.original_test = Test("microsleep 4000000\ninput tap 612 1100\nmicrosleep 4000000\n",0, self.pkg_name)

    def calculate_coverage(self, test):

        """
            Calculates the percentage of method coverage of a given test. 
            Method profiling is used to find how many methods are called 
            during the test, and that number is then compared against the 
            total number of methods in the app (under the main package name).
        """

        # profile app, get trace file, run get-run-methods.sh
        t1 = threading.Thread(target=self._start_profiling)
        t2 = threading.Thread(target=self._stop_profiling)
        t3 = threading.Thread(target=self._pull_tracefile) ### full cpu_jiffy file
        #t4 = threading.Thread(target=self._get_run_method_count)

        print("\n=================================================\n")
        print("Starting CPU profiling...")
        t1.start()
	#t1.join()
	time.sleep(2)   
	print "Now test will be running"
        duration=test.run()
	print "running completed"
      	t2.start()
        t2.join()
	time.sleep(5)
        print("\CPU profiling done.")
        #print("\n=================================================\n")
        print("Pulling CPU trace file from phone...")
	#time.sleep(5)
        t3.start()
        t3.join()
	time.sleep(1)
        print("\nTrace file retrieved.")

        #print("\n=================================================\n")
        #print("Getting unique number of methods called during test...")
        #t4.start()
        #t4.join()

        # get syscalls counts
        #count=0
	try:
		count=self.energy_estimation(duration)
      	except:
		count=0
        print("\nDone getting cpu counts\n")
       
        # calculate and set the coverage of test 
        test.set_coverage(count)### divide by duration if per second is wanted

    def increase_coverage(self, number_of_events):
	f_track=open(utils.TRACK_PATH+"track.txt","w")	
	f_track.write(str(utils.COUNTER))	
	f_track.close()
	utils.COUNTER=utils.COUNTER+1

        """
            Tries to increase coverage of current test by mutating
            it until the coverage is higher.
        """
        # Method 1:
        # Create 1 new tests
        tests = [self.generate_test(number_of_events) for i in range(1)] #### set 5.. modified for testing only, Shaiful
        #print "###############################"
	#print tests
	#print "###############################"
        # Choose highest coverage test
        highest = max(tests)
        print("Highest CPU jiffies for this round: " + str(highest.get_coverage()))
       
        if highest < self.test:
            print("CPU-utilization has gone down, ignoring this round of tests")
            return
 
        if highest >= self.test:
            self.test = highest
        """
        if self.prev_test == highest:
            self.repeat += 1
            print("Have had the same coverage " + str(self.repeat) \
                + " times now.")
        else:
            self.prev_test = highest

        if self.repeat >= 5: ### it was previously 10, modified by Shaiful Chowdhury
            print("Coverage doesn't seem to be improving. Reverting back to " \
                    + str(self.prev_test))
            # go back to script before getting stuck
            self.test = self.prev_test
            # self.test = self.original_test
            self.repeat = 0
	"""

        print("=================================================")
        print("Ending with test: " + str(self.test))
	
        return

## serious modification.. 

    def generate_test(self,number_of_events):
        """
            Generates a new test by mutating the current one
        """
        self.pid = clean_up(self.pkg_name, self.apk)

###	modified by shaiful, so that the new round of random tests start from the initial scripts again. 
########## toss is introduced because we found sometimes prefix helps and sometimes harms.. 
	toss=randint(0,1)
	if toss==1:
        	new_test = Test(Initial.test_script, app_pkg=self.pkg_name)
		number_of_events=number_of_events-7
	else:
		new_test = Test("", app_pkg=self.pkg_name)
	 #new_test = Test(self.test.get_initial_script(), app_pkg=self.pkg_name)

        print("\n=================================================\n")
        print("Creating new test...")

        # add random events
	
        for i in range(number_of_events):	    
            new_test.add_event(random.choice(EVENTS)(self.pkg_name).get_command())

        print("\nNew test created.") 

        print("\nCalculating new Utilization...")
        # get coverage of new test
        self.calculate_coverage(new_test)
        print("\nUtilization calculated. Test = " + str(new_test))

        return new_test

    def _start_profiling(self):
        #subprocess.call(["adb", "shell", "am profile " + self.pid + " stop"])
	subprocess.call("adb shell sh /sdcard/cpu_before.sh "+ self.pkg_name, shell=True)	
	#subprocess.call("adb shell sh /sdcard/strc_gen.sh "+ self.pkg_name, shell=True)

	
    def _stop_profiling(self):
        #subprocess.call(["adb", "shell", "am profile " + self.pid + " stop"])
	subprocess.call("adb shell sh /sdcard/cpu_jiffy.sh "+ self.pkg_name, shell=True)
	time.sleep(5)
	#subprocess.call("adb shell sh /sdcard/kill.sh "+ self.pkg_name, shell=True)
	subprocess.call("adb shell sh /sdcard/cpu_after.sh "+ self.pkg_name, shell=True)


    def _pull_tracefile(self):

	#subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/cpu_jiffy.txt"])	

        subprocess.call(["adb", "pull", "/sdcard/cpu_jiffy.txt", \
                        os.getcwd() + "/cpu_jiffy.txt"])
	subprocess.call(["adb", "pull", "/sdcard/sysInfo_before.txt", \
                        os.getcwd() + "/sysInfo_before.txt"])
	subprocess.call(["adb", "pull", "/sdcard/sysInfo_after.txt", \
                        os.getcwd() + "/sysInfo_after.txt"])
	#subprocess.call(["adb", "pull", "/sdcard/strace.txt", \
         #               os.getcwd() + "/strace.txt"])
	time.sleep(5)
	#subprocess.call("adb shell rm -f /sdcard/cpu_jiffy.txt")
	subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        +"cpu_jiffy.txt"])
	#subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
        #                +"strace.txt"])
	subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        +"sysInfo_after.txt"])
	subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        +"sysInfo_before.txt"])					 
	#print "trace_file retrieved"
	#time.sleep(20)
	   	
    #def _get_run_method_count(self):
     #   subprocess.call(SCRIPTS_PATH + "/get-run-methods.sh " \
      #          + os.getcwd() + "/output.trace" \
       #         + " " + self.pkg_name + " " + SCRIPTS_PATH, shell=True)


    def energy_estimation(self, Duration):

	### This is cpu-utilization based test generation
	fr=open("cpu_jiffy.txt","r")
	line=fr.readline().strip()
	
	data=re.findall('[^ ]+',line)
	cpu_jiffy_user=float(data[13])
	cpu_jiffy_kernel=float(data[14])
	return (cpu_jiffy_user+cpu_jiffy_kernel)

	### use the commented part when using GreenOracle for test generation.. 
	"""
	model={}
	fr=open("model.csv","r")
	line=fr.readline()
	lines=fr.readlines()
	for line in lines:
		line=line.strip()
		data=re.findall('[^\t]+',line)
		model[data[0]]={}
		model[data[0]]['weight']=float(data[1])/float(data[4])

		#model[data[0]]['min']=float(data[3])
		#model[data[0]]['max']=float(data[4])

	fr.close()
	
	energy=0	
	
	############	Capture energy from syscalls ######################
	Fsync=0
	Write=0
	Open=0
	fr=open("strace.txt","r")
	lines=fr.readlines()
	c=0
	for line in lines:
		c=c+1
		line=line.strip()
		data=re.findall('[^ ]+',line)
		if "recvfrom" in line:
			call=float(data[3])
			energy=energy+(call*model['recvfrom']['weight'])
		if "sendto" in line:
			call=float(data[3])	
			energy=energy+(call*model['sendto']['weight'])
		
		if "setsockopt" in line:
			call=float(data[3])
			energy=energy+(call*model['setsockopt']['weight'])
			
		if "mkdir" in line:
			call=float(data[3])	
			energy=energy+(call*model['mkdir']['weight'])
		if "futex" in line:
			call=float(data[3])			
			energy=energy+(call*model['futex']['weight'])
		if "unlink" in line:
			call=float(data[3])		
			energy=energy+(call*model['unlink']['weight'])
		#### for grouped syscalls

		if "write" in line or "pwrite" in line:
			Write=Write+float(data[3])
		if "fsync" in line or "fdatasync" in line:
			Fsync=Fsync+float(data[3])
		if "open" in line or "openat" in line:
			Open=Open+float(data[3])

	if c==0:
		fw=open(BASE_PATH+"strace_problem.txt","a")
		fw.write(self.pkg_name+ "\n")
		fw.close()	
		
		
	energy=energy+(Write*model['Write']['weight'])	
	energy=energy+(Fsync*model['Fsync']['weight'])	
	energy=energy+(Open*model['Open']['weight'])
	
        ########################## done energy with syscalls #################################

        ######### cpu and others #####################

	fr1=open("sysInfo_before.txt","r")
	fr2=open("sysInfo_after.txt","r")

	line1=fr1.readline().strip() ############# These numbers identify the amount of time the CPU has spent performing different kinds of work (before).
	data1=re.findall('[^ ]+',line1)
	line2=fr2.readline().strip()#############These numbers identify the amount of time the CPU has spent performing different kinds of work (after).
	data2=re.findall('[^ ]+',line2)
	User=(float(data2[1])-float(data1[1]))
		
	
	#################### ignore next two lines#######################
				
	line1=fr1.readline().strip()
	line1=fr1.readline().strip()
	line2=fr2.readline().strip()
	line2=fr2.readline().strip()
		##################################################################
	##########	read the interupt infos	

	line1=fr1.readline().strip()
	line2=fr2.readline().strip()	
	data1=re.findall('[^ ]+',line1)
	data2=re.findall('[^ ]+',line2)
	Intr=(float(data2[1])-float(data1[1]))

##########	read context switching####	

	line1=fr1.readline().strip()
	line2=fr2.readline().strip()
	data1=re.findall('[^ ]+',line1)
	data2=re.findall('[^ ]+',line2)
	CTXT=(float(data2[1])-float(data1[1]))
############## ignore btime ############

	line1=fr1.readline().strip()
	line2=fr2.readline().strip()

########## total processes running ####	

	line1=fr1.readline().strip()
	line2=fr2.readline().strip()	
	data1=re.findall('[^ ]+',line1)
	data2=re.findall('[^ ]+',line2)
	no_process=(float(data2[1])-float(data1[1]))
	fr1.close()
	fr2.close()		


	fr=open("cpu_jiffy.txt","r")
	line=fr.readline().strip()
	
	data=re.findall('[^ ]+',line)
	cpu_jiffy_user=float(data[13])
	Num_threads=(float(data[19]))
	Vsize=float(data[22])
	
	#normalized=(User-model['User']['min'])/(model['User']['max']-model['User']['min'])		
	#energy=energy+normalized*model['User']['weight']
############ This is special for cpu_jiffy_user, so that tests that goes outside have very less cpu ####

	energy=energy+(model['User']['weight']*cpu_jiffy_user) ### this is calculated using GreenOracle model table..  
	energy=energy+(CTXT*model['CTXT']['weight'])
	energy=energy+(Intr*model['Intr']['weight'])	
	energy=energy+(Num_threads*model['Num_threads']['weight'])	
	energy=energy+(Vsize*model['Vsize']['weight'])
	energy=energy+(Duration*model['Duration']['weight'])
	return (energy+41.96) ## with offset from GreenOracle
	"""

