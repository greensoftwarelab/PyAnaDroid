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

import sys, argparse, time
from libmutation import Test, TestMutator, utils, image_capture, initial
import os
import shutil
from os import listdir
import subprocess
import commands
from random import randint
import re

EVENT_PATH = "/dev/input/event1"



### this function converts a test script to a GreenMiner script.. 
def convert_to_gm(apk,package, activity):

	fr=open(utils.BEST_EMU_PATH+package+".sh","r")
	#fw=open(utils.BEST_TEST_PATH+apk[:-4]+".sh","w")	## if we want with apk name
	fw=open(utils.BEST_TEST_PATH+package+".sh","w")	## if we want with package name	
	lines=fr.readlines()

	#### write prefix ... 
	fw.write("# Wait for Wattlog\nmicrosleep 10000000\n# Load App\n{{{timing}}}\nam start -n ")
	fw.write(package+"/"+activity+"\n"+"microsleep 10000000\n")
	fw.write("{{{timing}}}\n")
	for line in lines:
		
		line=line.strip()
                if len(line)<1:
			continue
		if "HOME" in line:
			break
        	if "sleep" in line:
			bits = line.split()
			fw.write("microsleep "+str(int(bits[1])*1000000)+"\n")
			continue
	    	if line[0]=="#": ## this is comment
        		fw.write(line+"\n")
		
	    	else: ##### check for tap
			bits = line.split()
			if bits[1]=='tap':
				fw.write("tapnswipe "+EVENT_PATH+" tap "+str(bits[2])+" "+str(bits[3])+"\n")
			elif bits[1]=='swipe':
			#	duration=int(bits[6])####*1000
				fw.write("tapnswipe "+EVENT_PATH+" swipe "+str(bits[2])+" "+str(bits[3])+" "+str(bits[4])+" "+str(bits[5])+"\n")	
			else:
				fw.write(line+"\n")		 
	############# write postfix##################

	fw.write("### Exit Process\n{{{timing}}}\nmicrosleep 2000000\ninput keyevent HOME")	

        fw.close()
	

if __name__=='__main__':
    				
    f_track=open("track.txt","w") ###### this is a counter file which will be continously checked to see if the program is stalled.. 
    f_track.write(str(0))	
    f_track.close()	
    f_end=open("is_end.txt","w")######## set one when running is complete	
    f_end.write(str(0))	
    f_end.close() 	
    parser = argparse.ArgumentParser(description="Mutate a test")
    parser.add_argument('test', 
                        help="Starting test that will be mutated to get " \
                        + "higher coverage")
   
    args = parser.parse_args()

    ### a prefix script.. 		
    ob=initial.Initial(args.test)
    test_script=ob.get_initial_script()	
    #################
    COMPLETED={}	
    count=0
    for apk_file in listdir(utils.APKS_PATH):
		
			
			
		########### read all the completed apks to avoid repeatition
		f_apk_to_package=open(utils.APK_TO_PACKAGE+"apk_to_package.txt","r")
		lines=f_apk_to_package.readlines()
		for l in lines:
			data=re.findall("[^\t]+",l)
			
			if data[0] not in COMPLETED:
				COMPLETED[data[0]]=1

		if apk_file[:-4] in COMPLETED:
			continue

		### restart phone
		#if count==1:

		#	subprocess.call(["adb", "reboot"])
		#	time.sleep(100)
		
		#### this will enable (if not already) wifi before each app... 
		
		count=1
		print apk_file
		try:
			st=str(commands.getstatusoutput(utils.AAPT_PATH+"aapt dump badging "+utils.APKS_PATH+apk_file))
	 		start="package: name=\'"
			end="\' versionCode="
			package=((st.split(start))[1].split(end)[0])
			
			start="launchable-activity: name=\'"
			end="\'  label=\'"	
			main_activity=((st.split(start))[1].split(end)[0])
		#main_activity=main_activity.split(package+".",1)[1]

		# install and start app and find pid
	    		pid = utils.clean_up(package, utils.APKS_PATH+apk_file)
		except:
			count=0	
			continue

		# Copy test content
	    	
		################ addressing problematic apk that after trying four restart does notfinish
		### only useful when run with run.sh
		"""
		f_apk=open("track_apk.txt","r")
		val=int(f_apk.readline().strip())
		f_apk.close()
		if val>1:
			os.system("mv "+utils.APKS_PATH+apk_file+" "+utils.PROBLAMATIC_APKS+apk_file)	
			f_apk=open("track_apk.txt","w")
    			f_apk.write(str(0))
    			f_apk.close()
			utils.uninstall_app(package)
			continue

		val=val+1
		f_apk=open("track_apk.txt","w")
    		f_apk.write(str(val))
    		f_apk.close()
		""" 	
   
	    	old_test = Test(test_script, app_pkg=package)
    		mutator =  TestMutator(old_test, pid, package,utils.APKS_PATH+apk_file)
    		#mutator.calculate_coverage(old_test)  
			
                #### how many events for this app ? ###########
		number_of_events=randint(5,10)
		run_min=number_of_events
	
		###always keep within 15 to 20 mins######
		#if run_min<10:
		#	run_min=20
		#if run_min>30:
		run_min=5	
		print "This app will be tested for "+str(run_min)+" minutes" 
    		start = time.time()
    		while (time.time() - start) < (run_min*60):
			#print (time.time() - start), args.time

			### disable auto rotate 
			subprocess.call(["adb", "shell", " content insert --uri content://settings/system --bind name:s:accelerometer_rotation --bind value:i:0"])
			### Enable wifi.. for real device ###
			"""	
			subprocess.call("adb shell su -c service call bluetooth_manager 8", shell=True)
			time.sleep(5)
			subprocess.call(["adb", "shell", " am start -a android.intent.action.MAIN -n com.android.settings/.wifi.WifiSettings"])
			time.sleep(2)
			subprocess.call(["adb", "shell", " input keyevent 20"])
			time.sleep(2)
			subprocess.call(["adb", "shell", " input keyevent 23"])
			time.sleep(10)
			subprocess.call(["adb", "shell", " input keyevent HOME"])
			time.sleep(8)
			"""
        		mutator.increase_coverage(number_of_events)
			try:
				os.remove("sysInfo_after.txt")
				os.remove("sysInfo_before.txt")
				os.remove("cpu_jiffy.txt")
	       			os.remove("strace.txt")
			except:
				pass	
		
		f_duration=open(utils.DURATION_PATH+package+"_duration","w")
		f_duration.write(str(int(mutator.test.duration)+25)) ## 25 is added for wattlong, app load, and exit.. 
		f_duration.close()
   	 	shutil.copy2(utils.TESTS_PATH+"/"+mutator.test.name, utils.BEST_EMU_PATH+package+".sh")
		
    ########### compatible for GREENMiner #########
		print"=================================================================="
		print"=================================================================="
		print "Now running to capture images for the final test"
		
		while 1:
			utils.uninstall_app(package)
			utils.install_app(utils.APKS_PATH+apk_file)
			image_capture.capture_images(package)
			no_img=0
			for img in listdir(utils.IMAGE_PATH+package+"/"):
				no_img=no_img+1
			if no_img>=5:
				break
			else:
				print "Images were not captured properly"
				print"=================================================================="
				print"=================================================================="	

		
		print("Highest coverage test is: " + str(mutator.test))
    		print "Duration="+str(mutator.test.duration)
    
    		convert_to_gm(apk_file,package,main_activity)
		
		f_apk_to_package=open(utils.APK_TO_PACKAGE+"apk_to_package.txt","a")
		f_apk_to_package.write(str(apk_file[:-4])+"\t"+str(package)+"\t"+str(main_activity)+"\n")
		f_apk_to_package.close()

		f_apk=open("track_apk.txt","w")
    		f_apk.write(str(0))
    		f_apk.close()

    f_end=open("is_end.txt","w")		
    f_end.write(str(1))
    f_end.close() 		
