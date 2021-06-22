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

import time, os, subprocess, threading
import re
class CPU:
    
	def __init__(self):
		self.User=0
		self.CTXT=0
		self.Nice=0
		self.Mfaults=0	
		self.duration=0

		
	def cpu_before(self, pkg_name):
		subprocess.call("adb shell su -c \" sh /sdcard/cpu_before.sh \" "+ pkg_name, shell=True)		
	
	def cpu_after(self, pkg_name):
		subprocess.call("adb shell  su -c \" sh /sdcard/cpu_jiffy.sh\" "+ pkg_name, shell=True)
		subprocess.call("adb shell su -c \" sh /sdcard/cpu_after.sh\" "+ pkg_name, shell=True)	

	def pull_cpu(self, pkg_name):
		subprocess.call(["adb", "pull", "/sdcard/cpu_jiffy.txt", \
                        os.getcwd() + "/cpu_jiffy.txt"])
		subprocess.call(["adb", "pull", "/sdcard/sysInfo_before.txt", \
                        os.getcwd() + "/sysInfo_before.txt"])
		subprocess.call(["adb", "pull", "/sdcard/sysInfo_after.txt", \
                        os.getcwd() + "/sysInfo_after.txt"])
	
		
		subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        +"cpu_jiffy.txt"])

		subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        +"sysInfo_after.txt"])
		subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        +"sysInfo_before.txt"])	

	def count_cpu(self,apk):	

		fr1=open("sysInfo_before.txt","r")
		fr2=open("sysInfo_after.txt","r")
		f_tmp=open("CPU_check.txt","a")
		#### summary of first line ############	
		line1=fr1.readline().strip() ############# These numbers identify the amount of time the CPU has spent performing different kinds of work (before).
		data1=re.findall('[^ ]+',line1)
		line2=fr2.readline().strip()#############These numbers identify the amount of time the CPU has spent performing different kinds of work (after).
		data2=re.findall('[^ ]+',line2)

		self.User=self.User+(float(data2[1])-float(data1[1]))
		f_tmp.write(apk+"\t"+str((float(data2[1])-float(data1[1])))+"\n")
		f_tmp.close()
		self.Nice=self.Nice+(float(data2[2])-float(data1[2]))
		
		#################### ignore until interrupt lines#######################
		while 1:				
			line1=fr1.readline().strip()
			line2=fr2.readline().strip()
			if 'cpu' in line1:
				continue
			break
		##################################################################
	##########	read the interupt infos	

		#line1=fr1.readline().strip()
		#line2=fr2.readline().strip()	
		data1=re.findall('[^ ]+',line1)
		data2=re.findall('[^ ]+',line2)
		#dict_app[version]['tot_intrpt']=dict_app[version]['tot_intrpt']+(float(data2[1])-float(data1[1]))

##########	read context switching####	

		line1=fr1.readline().strip()
		line2=fr2.readline().strip()
		data1=re.findall('[^ ]+',line1)
		data2=re.findall('[^ ]+',line2)
		self.CTXT=self.CTXT+(float(data2[1])-float(data1[1]))
		############## ignore btime ############

		line1=fr1.readline().strip()
		line2=fr2.readline().strip()

########## total processes running ####	

		line1=fr1.readline().strip()
		line2=fr2.readline().strip()	
		data1=re.findall('[^ ]+',line1)
		data2=re.findall('[^ ]+',line2)
		fr1.close()
		fr2.close()	


		fr=open("cpu_jiffy.txt","r")
		line=fr.readline().strip()
		data=re.findall('[^ ]+',line)

		
		self.Mfaults=self.Mfaults+float(data[11])
		fr.close()
		#os.system("rm -f sysInfo_before.txt")
		#os.system("rm -f sysInfo_after.txt")
		os.system("rm -f cpu_jiffy.txt")

		
		
