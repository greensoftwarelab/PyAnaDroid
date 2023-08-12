# Requirements for PyAnaDroid

## Overview
Anadroid is a tool capable of automating the process of analyzing and benchmarking Android applications' energy consumption, using state-of-the-art energy analysis tools. 
Anadroid can be configured to use different energy profilers and test frameworks in its execution pipeline, being able to perform automatic instrumentation and building of application source code. 
It can be used to perform both white-box and black-box testing.
To use this package, you need to have Python installed, and you can install it via `pip`. Additionally, there are some dependencies that you should be aware of.

## System Requirements
- *Nix-based OS;
- Python 3.6 or later;
- pip (Python package installer);
- Android SDK;
- ~120 MB of disk space;


## Installation
1. Open a terminal or command prompt.
2. Install the package using pip:
   ```bash
   pip install anadroid
   ```

## Dependencies:

```
androguard==3.4.0a1
incremental>=17.5.0
lxml==4.6.5
six>=1.15.0
manafa>=0.3.127
physalia==0.0.1.dev122
termcolor==1.1.0
pylogcatparser>=0.2.7
androidviewclient==22.5.1
```

## Usage 

```
from anadroid.Anadroid import AnaDroid

folder_of_app = "demoProjects/SampleApp"
anadroid = AnaDroid(folder_of_app, testing_framework=TESTING_FRAMEWORK.MONKEY)
anadroid.defaultWorkflow()
```

## Testing requirements

```
 python3 -m unittest 
```

## Contributing Guidelines

Contributions to PyAnaDroid Package are welcome!

## License 

This package is released under the MIT License.




