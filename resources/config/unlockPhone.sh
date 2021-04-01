#!/bin/bash




# Implementations

# Tested only with NEXUS 5 
function unlockWithMenuButtonOnly(){
	# https://developer.android.com/reference/android/view/KeyEvent.html#KEYCODE_MENU
	adb shell input keyevent 26 #Pressing the lock button
	adb shell input keyevent 82 # KEYCODE_MENU
}

function unlockWithPasscode(){
	adb shell input keyevent 26 #Pressing the lock button
	adb shell input touchscreen swipe 930 880 930 380 #Swipe UP
	adb shell input text "<your - password - here >" #Entering your passcode
	adb shell input keyevent 66 #Pressing Enter
}

# Instructions: leave uncommented the desired approach 

unlockWithMenuButtonOnly
# unlockWithPasscode

