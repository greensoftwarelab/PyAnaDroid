
RERAN
=====
Record and Replay for Android

(c)  Copyright 2011-2013

The preferred license for RERAN is the BSD License.

### Requirements

- Android SDK
- Rooted android device
- C compiler
- CMake
- Python 
- At least one eye and something to type (a finger, maybe?)


#### Getting Started

Getting started with RERAN is easy. The instructions below assume you
have the Android SDK installed on your computer (runs on Linux, Mac, 
and Windows). We use the adb debugging bridge to push files onto the 
phone and run the record and replay commands. The adb tool is in the 
/platform-tools folder of the SDK folder you install. In order to call this tool from anywhere on your workstation, you should set the following environment variables:

```
	export ANDROID_HOME=$HOME/android-sdk/ 
 	export PATH=$ANDROID_HOME/platform-tools:$PATH
```  




The example below 
performs our standard record and replay. For the selective replay and 
time-warping features, please see their respective pages.



#### RERAN Design

First, recording with getevent will create a log of the events used 
during the run, e.g., recordedEvents.txt. Second, send the recorded 
log into the Translate program. The Translate program will output a 
translated log of the original events. Third, push the translated 
log, e.g., translatedEvents.txt, onto the phone. Fourth, run the Replay 
program using the adb shell.


#### ARM Cross-compiler

In order for the replay program to run on Android devices, they must be compiled using a cross-compiler for ARM CPU's. The most easy way to do this is using CMAKE (https://cmake.org/), that is bundled with android-ndk. 

build.sh file automatically detects both ABI and API level of the connected device (through ADB), being able to invoke CMAKE to generate the suitable replay executable for such device.

However, if you want to do things in the old way, you can follow the original RERAN instructions: https://www.androidreran.com/software.php 

#### Setup

First you must build the Translate JAR and the replay executable:

```
   ./build.sh
   cd build
   make
```  

This script will generate those files and the adequate replay executable to be 
installed in your device

### Record session on the connected device
To start recording the testing session, execute the following command:

```
$ python src/RERANWrapper.py record <app_id> <output_filename>
```  

This command will make the program wait for any key press to explicitly terminate the testing session.

### Install recorded files on device

```
$ python src/RERANWrapper.py  push  <filename>
```  

### Replay recorded session 

```
$ python src/RERANWrapper.py replay <app_id> <output_filename>
```  




Please see the website www.androidreran.com for more info.