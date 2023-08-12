# AnaDroid
[![Build Status](https://travis-ci.com/RRua/pyAnaDroid.svg?branch=main)](https://travis-ci.com/RRua/pyAnaDroid)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![PyPI version](https://badge.fury.io/py/anadroid.svg)](https://badge.fury.io/py/anadroid)
[![PyPI license](https://img.shields.io/pypi/l/ansicolortags.svg)](https://pypi.python.org/pypi/anadroid)
[![PyPI status](https://img.shields.io/pypi/status/ansicolortags.svg)](https://pypi.python.org/pypi/anadroid)
[![DOI](https://zenodo.org/badge/459944500.svg)](https://zenodo.org/badge/latestdoi/459944500)



Anadroid is a tool capable of automating the process of analyzing and benchmarking Android applications' energy consumption, using state-of-the-art energy analysis tools. Anadroid can be configured to use different energy profilers and test frameworks in its execution pipeline, being able to perform automatic instrumentation and building of application source code. It can be used to perform both white-box and black-box testing.
## Documentation

https://greensoftwarelab.github.io/PyAnaDroid/anadroid.html#

## Video Demo

https://greensoftwarelab.github.io/PyAnaDroid/anadroid.html#

## Use cases
- Application Benchmarking: Replicating test work/procedures on different applications to carry out comparative studies of energy consumption.
- Detection of energy hotspots in application code;
- Detection of energy-greedy coding practices;
- Calibration of energy consumption prediction models;
- Many others.  

## Supported Test Frameworks
- JUnit-based frameworks (Robotium, Espresso, JUnit);
- Application UI/Exerciser Monkey;
- Monkeyrunner;
- DroidBot;
- App Crawler;
- RERAN;
- Monkey++ (soon).

## Supported energy profilers:
- Trepn Profiler;
- Manafa;
- GreenScaler;
- Monsoon (soon);
- Petra (soon).


# Workflow

By default, Anadroid is configured to perform white-box testing of applications, instrumenting its code (Java and/or Kotlin), in order to collect tracing of the methods invoked during application execution and estimate the energy consumed by these. After the instrumentation phase, a project is created in the original directory, which is a copy of it, with the code and build scripts already instrumented. Then, the source code and apk are built from the sources of the instrumented project (both debug and release builds are supported), and the application is installed on the device. After installation, the energy profiler is enabled and the application tests are executed. At the end of the process, the monitoring process is stopped and its results collected, and the application is uninstalled.

![Anadroid Workflow](AnaDroid.png)

# Installation:

## Using python-pip
```
$ pip install anadroid
```

## From sauce

```
$ git clone --recurse-submodules https://github.com/greensoftwarelab/pyanadroid.git
```


# Examples


## Plug-and-play execution

```
$ usage: pyanadroid [-h] [-t {Monkey,Monkeyrunner,JUnit,RERAN,Espresso,Robotium,Crawler,Droidbot,Custom,Other}] [-p {Trepn,GreenScaler,Petra,Monsoon,E-manafa,None}]
               [-b {Release,Debug,Custom}] [-i {JInst,Hunter,None}] [-it {MethodOriented,TestOriented,'ActivityOriented',),AnnotationOriented,None}]
               [-a {MethodOriented,TestOriented,('ActivityOriented',,AnnotationOriented,None}] [-d DIRETORY] [-bo] [-record] [-run] [-rb] [-ri] [-ja] [-sc {USB,WIFI}]
               [-ds DEVICE_SERIAL] [-td TESTS_DIR] [-n PACKAGE_NAMES [PACKAGE_NAMES ...]] [-apk APPLICATION_PACKAGES [APPLICATION_PACKAGES ...]] [-rec] [-cmd COMMAND]
               [-nt N_TIMES]

optional arguments:
  -h, --help            show this help message and exit
  -t {Monkey,Monkeyrunner,JUnit,RERAN,Espresso,Robotium,Crawler,Droidbot,Custom,Other}, --testingframework {Monkey,Monkeyrunner,JUnit,RERAN,Espresso,Robotium,Crawler,Droidbot,Custom,Other}
                        testing framework to exercise app(s)
  -p {Trepn,GreenScaler,Petra,Monsoon,E-manafa,None}, --profiler {Trepn,GreenScaler,Petra,Monsoon,E-manafa,None}
                        energy profiler
  -b {Release,Debug,Custom}, --buildtype {Release,Debug,Custom}
                        app build type
  -i {JInst,Hunter,None}, --instrumenter {JInst,Hunter,None}
                        Source code instrumenter
  -it {MethodOriented,TestOriented,('ActivityOriented',),AnnotationOriented,None}, --instrumentationtype {MethodOriented,TestOriented,('ActivityOriented',),AnnotationOriented,None}
                        instrumentation type
  -a {MethodOriented,TestOriented,('ActivityOriented',),AnnotationOriented,None}, --analyzer {MethodOriented,TestOriented,('ActivityOriented',),AnnotationOriented,None}
                        results analyzer
  -d DIRETORY, --diretory DIRETORY
                        app(s)' folder
  -bo, --buildonly      just build apps
  -record, --record     record test
  -run, --run_only      run only
  -rb, --rebuild        rebuild apps
  -ri, --reinstrument   reinstrument app
  -ja, --justanalyze    just analyze apps
  -sc {USB,WIFI}, --setconnection {USB,WIFI}
                        set connection to device and exit
  -ds DEVICE_SERIAL, --device_serial DEVICE_SERIAL
                        device serial id
  -td TESTS_DIR, --tests_dir TESTS_DIR
                        tests directory
  -n PACKAGE_NAMES [PACKAGE_NAMES ...], --package_names PACKAGE_NAMES [PACKAGE_NAMES ...]
                        package(s) of already installed apps
  -apk APPLICATION_PACKAGES [APPLICATION_PACKAGES ...], --application_packages APPLICATION_PACKAGES [APPLICATION_PACKAGES ...]
                        path of apk(s) to process
  -rec, --recover       recover progress of the previous run
  -cmd COMMAND, --command COMMAND
                        test command
  -nt N_TIMES, --n_times N_TIMES
                        times to repeat test (overrides config)

```


## From Sauce


### Execute a simple Monkey test over an application

By default, Anadroid uses Manafa profiler to estimate energy consumption. The Monkey test (or any other test with other supported testing framework) and its parameters can be configured by modifying the .cfg present in the resources/testingFrameworks/<framework> directory. The results are stored in the results/<app_id>/<app_version> directory

```
from anadroid.Anadroid import AnaDroid

folder_of_app = "demoProjects/SampleApp"
anadroid = AnaDroid(folder_of_app, testing_framework=TESTING_FRAMEWORK.MONKEY)
anadroid.defaultWorkflow()
```


## Working Examples


### Example 1 - Using DroidBot to automatically test an Android project(s) and monitor its energy consumption (from command-line)

```
$ pyanadroid -d projects_dir> -t Droidbot
```

### Example 2 - Perform a custom test (e.g touch app screen)

```
$ pyanadroid -d <projects_dir> -t Custom -cmd 'adb shell input touchscreen tap 500 500'
```

###  Example 3 - Extend PyAnaDroid workflow to perform 

#### 1) Create a new subclass of the AnaDroid class and implement and override the default_workflow method 

```
from anadroid.Anadroid import AnaDroid

class MyCustomAnaDroidWorkflow(AnaDroid):

  def default_workflow():
    # example: reboot device after each test suite
    super(AnaDroid, self).default_workflow()
    self.device.reboot()    

```

#### 2) Invoke the new custom workflow

```
custom_wkflow = MyCustomAnaDroidWorkflow()
custom_wkflow.defaultWorkflow()

```

###  Example 4 - Skip instrumentation and building phase and perform black-box analysis only over the apks.
Note: the process will still be monitored using the profiler but the performance metrics will only be given at the test level (e.g. the energy consumption of each test execution).

```
$ pyanadroid -d <projects_dir> -run -t Custom 'adb shell input touchscreen tap 500 500'
```

PyAnaDroid produces a large amount of results from the analysis it does on its execution blocks. These results are stored in the form of files in specific directories. For each execution of a certain version of a certain app, a subdirectory is created in the directory anadroid_results/\<app-name\>--\<app-package\>/\<app-version\> where all the results of the analyzes carried out on the applications will appear. For each execution of a test framework on an application, a subdirectory \<testing-framework\>\<instrumentation-type\>\<timestamp\> is created inside the previous directory and that contains the results related to that execution. The result files are as follows:
- tests_index.json: contains the list of files associated with each test run, identified by test id.
- test_\<test-id\>.logcat: contains device logs captured during test execution;
- test_\<test-id\>_logresume.json: contains a summary made from the analysis of the logs contained in the file test_<test-id>.logcat. It has metrics such as the number of exceptions thrown, fatal or error log messages, etc.
- device.json: contains the specs of the device where the tests were conducted (brand, model, ram, cpu cores, serial nr, etc)
- manafa_resume_<test_id>.json: contains test-level performance metrics reported by E-Manafa (if used);
- functions_\<timestamp\>.json: contains performance metrics for each of the executed functions/methods of the app in a certain test.
- trace-\<timestamp\>-\<timestamp\>.systrace: contains the cpu frequency changes logged during a certain test id;
