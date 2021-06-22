#!/bin/bash


trap=0
#echo "0" > track_apk.txt
while :
do

	last=-1
	kill $(ps aux | grep 'Green' | awk '{print $2}')
	ps aux | grep -ie GreenScaler | awk '{print $2}' | xargs kill -9
	/home/shaiful/android/android-sdk-linux/tools/emulator -avd GreenScaler -partition-size 512 &
	sleep 60
	if [ $trap = 1 ]
		then 
			trap=0
			adb reboot
			sleep 60

			
		fi
	#sh ~/gitlab_repos/green-star/utils/root-android/root.sh

        python mutator_main.py script.sh &	
        pid=$(ps -ef| grep mutator_main.py)

	while :
	do
	
		echo last=$last >> log_run.txt
		sleep 900
 		next=`cat track.txt`
		echo next=$next >> log_run.txt

		if [ $last = $next ]
		then
   			ps aux | grep -ie mutator_main | awk '{print $2}' | xargs kill -9
			echo "killed process" >> log.txt
			#kill $!
			trap=1
			sleep 10
			break			
		else
			echo "running properly"
			last=$next

		fi
	
		end=`cat is_end.txt`
		if [ $end = 1 ]
		then 
			break
			
		fi
	done

	if [ $end = 1 ]

	then 
		echo "all programs done"
		break
			
	fi


done
