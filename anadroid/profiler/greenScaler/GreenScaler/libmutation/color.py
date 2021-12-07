import time, os, subprocess, threading
import re
import anadroid.profiler.greenScaler.GreenScaler.libmutation.utils
from os import listdir
from PIL import Image

from anadroid.profiler.greenScaler.GreenScaler.libmutation import utils


class RGB:
	
	def __init__(self, package):
		self.r=0
		self.g=0
		self.b=0
		self.package=package

	def makedir(self):
		subprocess.call(["adb", "shell", "rm -rf", "/sdcard/screen_shots"])	
		time.sleep(3)
		subprocess.call(["adb", "shell", "mkdir", "/sdcard/screen_shots"])


	def run_screencap(self):
		subprocess.call("adb shell sh /sdcard/screen_capture.sh "+ self.package, shell=True)


	def pull_images(self):
		if os.path.exists(utils.IMAGE_PATH+self.package):
			os.system("rm -rf "+utils.IMAGE_PATH+self.package)
		os.system("mkdir "+utils.IMAGE_PATH+self.package)
		subprocess.call("adb pull /sdcard/screen_shots/ "+utils.IMAGE_PATH+self.package, shell=True)
		if not os.path.exists(utils.IMAGE_PATH+self.package+"/screen_shots"):
			os.system("mkdir "+utils.IMAGE_PATH+self.package+"/screen_shots")
			os.system("mv "+utils.IMAGE_PATH+self.package+"/* "+utils.IMAGE_PATH+self.package+"/screen_shots/")

	def delete_images(self):
		subprocess.call(["adb", "shell", "rm", "-rf", "/sdcard/screen_shots"])


	def capture_images(self):
		t1 = threading.Thread(target=self.run_screencap)
		print ("making directory to /sdcard/")
		self.makedir()
		print( "screencap started")
		t1.start()
		time.sleep(3)	

			

	def calculate_rgb(self):
		print ("=================================\n")
		print ("Now calculating RGB\nThis may take time based on test duration\n")
		print ("=================================\n")

		tot_R=0
		tot_G=0
		tot_B=0	
		no_image=0	
		for image in listdir(utils.IMAGE_PATH+self.package+"/screen_shots/"):
			print("image" + str(image))
			R=0
			G=0
			B=0

			try: ### to ignore incompletely downloaded image
				im = Image.open(utils.IMAGE_PATH+self.package+"/screen_shots/"+image)
				
				pixels = list(im.getdata())
				count=0
				for pix in pixels:
					r=pix[0]
					g=pix[1]
					b=pix[2]
					R=R+r
					G=G+g
					B=B+b
					count=count+1
				no_image=no_image+1	
			
			except:
				continue

			tot_R=tot_R+(R/count)	
			
			tot_G=tot_G+(G/count)
			tot_B=tot_B+(B/count)

		if no_image==0:
			print("empty screenshots")
			no_image=1
		self.r=tot_R/no_image
		self.g=tot_G/no_image
		self.b=tot_B/no_image
		os.system("rm -rf "+utils.IMAGE_PATH+self.package)
