import os
import sys
from subprocess import call, check_output, Popen, PIPE
from multiprocessing import Process
import os.path as path

default_tests_path="./tests/"
translate_jar_path="./build/RERANTranslate.jar"
replay_bin_path="./build/replay"

def record_events(filename):
	cmd = "adb shell getevent -t > " + filename
	pipes = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
	std_out, std_err = pipes.communicate()
	pipes.wait()

def pushToDevice(in_name):
	filename=path.basename(in_name)
	os.system("adb push " + in_name + " /sdcard/" + filename)
	os.system("adb push " + replay_bin_path + " /sdcard/")
	os.system("adb shell su -c \" cp /sdcard/" +filename+ " /data/local/ \"" )
	os.system("adb shell su -c \" cp /sdcard/replay" + " /data/local/ \"" )
	os.system("adb shell su -c \" chmod 777  /data/local/replay\"")

def replay(app_id,in_name):
	filename=path.basename(in_name)
	# run replay program with 0 delay time
	os.system("adb shell su -c \" /data/local/./replay /data/local/" + filename+ " 0\"" )



def translate_events(fileDir, filename):
	new_file="translated_" + filename
	os.system("java -jar "+ translate_jar_path + " " + fileDir + "/"+filename  + " "+ fileDir + "/" + new_file)
	return fileDir + "/"+ new_file


def record(app_id,out_name):
	#check if exists directory for this app
	dirname=default_tests_path+"/"+app_id
	if not os.path.isdir(dirname):
		os.mkdir(dirname)

	# creates killable process that runs record_events function, since there isnt an easy way to kill threads in python
	p=Process(target=record_events, args=(str(dirname+"/"+out_name),))
	p.start()
	val = raw_input("press any key to stop recording")
	p.terminate()
	new_file = translate_events(str(dirname), out_name)
	print( "translated events to " + new_file)
	return new_file

if __name__ == "__main__":
	if len(sys.argv)>3:
		task_name=sys.argv[1]
		app_id=sys.argv[2]
		io_filename=sys.argv[3]
		if task_name == "record":
			record(app_id,io_filename)
		elif task_name == "replay":
			replay(app_id, io_filename)
		elif task_name == "push":
			pushToDevice( io_filename)
		elif task_name == "all":
			new_file = record(app_id,io_filename)
			pushToDevice(new_file)
			replay(app_id,new_file)
	else:
		print("bad arg len. Required: RERAN_Test.py <task> <app_id> <input_file or output_file>")


	
