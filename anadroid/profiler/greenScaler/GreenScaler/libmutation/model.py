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

import os.path

import anadroid.profiler.greenScaler.GreenScaler.libmutation.utils
####### models coefficients
User=0.010338307844
Nice=0.00866181875175
CTXT=0.000076047702883
Mfaults=0.0111696167627
duration=0.629849024454
r=0.000500138296704
g=0.000390395800515
b=0.000519078649948
Fsync=0.00131024146096
bind=0.0603288971452
recvfrom=0.0000526086555484
sendto=0.0176077071287
Dup=0.0540600720362
Poll=0.00291918778915

def estimate_energy(apk, app, n):
	apk=apk[:-4]
	if not os.path.isfile(utils.BASE_PATH+"/dest/report/energy_report.csv"):
		fw=open(utils.BASE_PATH+"/dest/report/energy_report.csv","a")
		fw.write("\tUser_cpu\tNice_cpu\tContext_switches\tMajor_faults\tDuration\tRed\tGreen\tBlue\t")
		fw.write("Fsync\tbind\trecvfrom\tsendto\tDup\tPoll\tTotal_energy(j)\n")
	else:
		fw=open(utils.BASE_PATH+"/dest/report/energy_report.csv","a")

	fw.write(apk+"\t")
	energy=0.0
	energy=energy+(app.cpu.User*User/n)
	fw.write(str(app.cpu.User/n)+"/"+str(app.cpu.User*User/n)+"\t")
	energy=energy+(app.cpu.Nice*Nice/n)
	fw.write(str(app.cpu.Nice/n)+"/"+str(app.cpu.Nice*Nice/n)+"\t")
	energy=energy+(app.cpu.CTXT*CTXT/n)
	fw.write(str(app.cpu.CTXT/n)+"/"+str(app.cpu.CTXT*CTXT/n)+"\t")
	energy=energy+(app.cpu.Mfaults*Mfaults/n)
	fw.write(str(app.cpu.Mfaults/n)+"/"+str(app.cpu.Mfaults*Mfaults/n)+"\t")
	energy=energy+((app.cpu.duration/n)*duration)	
	fw.write(str((app.cpu.duration/n))+"/"+str((app.cpu.duration/n)*duration)+"\t")
	
	energy=energy+(app.color.r*r*(app.cpu.duration/n))
	fw.write(str(app.color.r*(app.cpu.duration/n))+"/"+str(app.color.r*r*(app.cpu.duration/n))+"\t")
	energy=energy+(app.color.g*g*(app.cpu.duration/n))
	fw.write(str(app.color.g*(app.cpu.duration/n))+"/"+str(app.color.g*g*(app.cpu.duration/n))+"\t")
	
	energy=energy+(app.color.b*b*(app.cpu.duration/n))
	fw.write(str(app.color.b*(app.cpu.duration/n))+"/"+str(app.color.b*b*(app.cpu.duration/n))+"\t")
	energy=energy+(app.syscall.Fsync*Fsync/n)
	fw.write(str(app.syscall.Fsync/n)+"/"+str(app.syscall.Fsync*Fsync/n)+"\t")
	energy=energy+(app.syscall.bind*bind/n)
	fw.write(str(app.syscall.bind/n)+"/"+str(app.syscall.bind*bind/n)+"\t")
	energy=energy+(app.syscall.recvfrom*recvfrom/n)
	fw.write(str(app.syscall.recvfrom/n)+"/"+str(app.syscall.recvfrom*recvfrom/n)+"\t")
	energy=energy+(app.syscall.sendto*sendto/n)
	fw.write(str(app.syscall.sendto/n)+"/"+str(app.syscall.sendto*sendto/n)+"\t")
	energy=energy+(app.syscall.Dup*Dup/n)
	fw.write(str(app.syscall.Dup/n)+"/"+str(app.syscall.Dup*Dup/n)+"\t")
	energy=energy+(app.syscall.Poll*Poll/n)
	fw.write(str(app.syscall.Poll/n)+"/"+str(app.syscall.Poll*Poll/n)+"\t")
	fw.write(str(energy)+"\n")
	fw.close()
	return energy
