
RERAN
=====
Record and Replay for Android

(c)  Copyright 2011-2013

The preferred license for RERAN is the BSD License.

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


#### Running Example

First you must build the Translate JAR and the replay executable:

```
   ./build.sh
   cd build
   make
```  


Push replay tool onto the phone: "/data/local" will be our local 
directory on the phone for the RERAN files. If it does not exist, it 
will be created. This step only needs to be done once.
```
   adb push ./replay /data/local
```    

Record a trace: The getevent tool is part of the Android SDK. The "-t" 
flag is to timestamp each event (used by the Translator in the next step).
```
    adb shell getevent -t > recordedEvents.txt
```    

Run the Translate program: The first two arguments of the Translate 
program are the path to the recorded events and the name of the translated 
events to output, respectively. There are also extra flags: see selective 
replay and time-warping.

```
    cd build/
    
    java -jar RERANTranslate.jar /path/to/recordedEvents.txt  /path/to/translatedEvents.txt
```    

Push the translated recorded events onto the phone:
```
	adb push  /path/to/translatedEvents.txt /data/local
```    

Run the replay program (after your app is setup): See setting up your 
app for more info.
```
    adb shell /data/local/./replay /data/local/translatedEvents.txt
```    

Please see the website www.androidreran.com for more info.