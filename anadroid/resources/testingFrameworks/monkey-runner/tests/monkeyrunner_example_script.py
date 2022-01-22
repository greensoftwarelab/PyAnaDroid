# -*- coding: utf-8 -*-
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice
from com.android.monkeyrunner.easy import EasyMonkeyDevice
from os import sys
import time


def dummy_test( pack_name):
	device = MonkeyRunner.waitForConnection()
	device.shell("monkey -p "+pack_name +" -c android.intent.category.LAUNCHER 1")
	time.sleep(2)
	#easydevice = EasyMonkeyDevice(device)
	#easydevice.type( 'id/batata_edit', 'batata')
	result = device.takeSnapshot()
	result.writeToFile(  pack_name+ "_main.png",'png')


if __name__== "__main__":
	if len(sys.argv) >0:
		dummy_test( sys.argv[1])
	else:
		print ("at least 1 args required ( <package-name>  )")
