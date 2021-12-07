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
import anadroid.profiler.greenScaler.GreenScaler.libmutation.utils
class SYSCALL:
    
	def __init__(self, package):
		self.Fsync=0
		self.bind=0
		self.recvfrom=0
		self.sendto=0
		self.Dup=0
		self.Poll=0
		self.package=package

	def syscall_capture(self):
		t1 = threading.Thread(target=self.start_profiling)
		t1.start()
		time.sleep(2)   	
	def start_profiling(self):
		
        	subprocess.call("adb shell su -c \" sh /sdcard/strc_gen.sh \" "+ self.package, shell=True)

	def syscall_stop(self):
		subprocess.call("adb shell su -c \" sh /sdcard/kill.sh \" "+ self.package, shell=True)
		utils.stop_app(self.package)
		#utils.uninstall_app(self.package)

	def pull_syscall(self):
		subprocess.call(["adb", "pull", "/sdcard/strace.txt", \
                        os.getcwd() + "/strace.txt"])
		subprocess.call(["adb", "shell", "rm", "-f", "/sdcard/" \
                        +"strace.txt"])
	
	def count_syscall(self):
		try:
			fr=open("strace.txt","r")
			lines=fr.readlines()
			for line in lines:
				line=line.strip()
				data=re.findall('[^ ]+',line)
				sys=data[len(data)-1]
				if "recvfrom" == sys:
					self.recvfrom=self.recvfrom+float(data[3])
				if "sendto" == sys:
					self.sendto=self.sendto+float(data[3])	
				if "bind" == sys:
					self.bind=self.bind+float(data[3])
				if ("dup" == sys) or ("dup2" == sys) or ("dup3" == sys):
					self.Dup=self.Dup+float(data[3])
				if ("fsync" == sys) or ("fdatasync" == sys):
					self.Fsync=self.Fsync+float(data[3])
				if ("poll" == sys) or ("ppoll" == sys):
					self.Poll=self.Poll+float(data[3])
			time.sleep(1)
			os.system("rm -f strace.txt")
			return 1
		except:
			return 0	
