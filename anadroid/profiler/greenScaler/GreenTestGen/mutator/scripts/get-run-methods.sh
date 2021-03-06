#!/bin/bash  
# Copyright 2014 Stephanie Gil (sgil@ualberta.ca)
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# What does this file do?
# ======================
# Given a trace file, finds all the methods called during a run that fall under
# the given package name. The output will be the number of methods called, not the 
# methods themselves.  
# For questions, contact Stephanie Gil (sgil@ualberta.ca)

TRACE_FILE=$1
PKG_NAME=$2
UTILS_PATH=$3

if [ $# != 3 ]; 
then
    echo "Missing parameters: ./get-run-methods.sh <tracefile> <app-package-name> <utils_path>"
else
    
    /home/shaiful/android/android-sdk-linux/platform-tools/dmtracedump -o $TRACE_FILE | grep "$PKG_NAME" > result.txt
    python $UTILS_PATH/count_unique_methods.py
fi


