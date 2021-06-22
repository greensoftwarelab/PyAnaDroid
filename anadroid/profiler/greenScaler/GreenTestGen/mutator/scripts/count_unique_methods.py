"""
Copyright 2014 Stephanie Gil (sgil@ualberta.ca)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


What this file does:
    Goes through result.txt, which is the output of get-run-methods.sh containing all the methods
    called during a test run of an apk, and parses it to find only the unique number of methods
    called. 
"""

import sys
import time
if __name__=='__main__':
    try:
        f_in = open("result.txt", "r")
        methods = []
	
        for line in f_in:
            if len(line.split()) < 1:
                continue
            bits = line.split()  # 4th element contains the method name
            method = bits[3].strip('.')
            if method in methods:
                continue
            else:
                methods.append(method)
                print(method)  # Only for viewing methods

        print("Total number of unique methods: " + str(len(methods)))
        f_out = open("run_methods.txt", "w")
	time.sleep(2)
        f_out.write(str(len(methods)))
        f_out.close()
    except IOError as e:
        print("Error opening result.txt")
        print(str(e))
        sys.exit()
