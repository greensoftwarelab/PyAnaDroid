import os

import json, math
from os import listdir
import sys
from pylab import average

def get_avg(l):
    ret_val = None
    try:
        ret_val = average(l)
    except:
        pass
    return ret_val


def from_file(filepath):
    js = {}
    with open(filepath, 'r') as jj:
         js = json.load(jj)
    return js


def aggregate_test_stats(lookup_dir): # /Users/ruirua/repos/pyAnaDroid/anadroid_results/SampleApp--com.example.sampleapp/1.0.0/DroidbotAnnotation_17_05_22_13_11_14
    manafa_resume_files = [ os.path.join(lookup_dir, f) for f in listdir(lookup_dir) if 'manafa_resume' in f]
    manafa_resume_objs = [from_file(f) for f in manafa_resume_files]
    print(f"how many files? {len(manafa_resume_objs)}")
    total_energys = list(map(lambda x: x['global']['total_energy:'], manafa_resume_objs))
    cpu_energys = list(map(lambda x: x['global']['per_component_consumption']['cpu'], manafa_resume_objs))
    elapseds = list(map(lambda x: x['global']['elapsed_time'], manafa_resume_objs))
    print(f"avg total consumption: {get_avg(total_energys)}")
    print(f"avg cpu consumption: {get_avg(cpu_energys)}")
    print(f"avg duration: {get_avg(elapseds)}")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        aggregate_test_stats(sys.argv[1])
    else:
        print("error. provide input dir")