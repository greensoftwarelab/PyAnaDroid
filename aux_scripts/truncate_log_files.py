

"""truncates log files"""

import json
import math
import os
from os import listdir
import time
from subprocess import TimeoutExpired, Popen, PIPE
from logcatparser.logCatParser import LogCatParser
from pylab import *

from textops import find, cat

from anadroid.application.AndroidProject import AndroidProject

TFS_TO_PROCESS = ['Monkey', 'Droidbot']
APP_INSTR = 'Annotation'

def execute_shell_command(cmd, args=[], timeout=None):
    command = cmd + " " + " ".join(args) if len(args) > 0 else cmd
    out = bytes()
    err = bytes()
    #print(command)
    proc = Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    try:
        out, err = proc.communicate(timeout=timeout)
    except TimeoutExpired as e:
        print("command " + cmd + " timed out")
        out = e.stdout if e.stdout is not None else out
        err = e.stderr if e.stderr is not None else err
        proc.kill()
        proc.returncode = 1
    return proc.returncode, out.decode("utf-8"), err.decode('utf-8')

def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split(os.sep))
    res = find(basedir, pattern=pattern, only_files=type_file == 'f', only_dirs=type_file == 'd')
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split(os.sep)) <= maxdepth + basedir_len, res))



def get_avg(l):
    ret_val = None
    try:
        ret_val = average(l)
    except:
        pass
    return ret_val


def to_int(val):
    ret_val = None
    try:
        ret_val = int(val)
    except:
        pass
    return ret_val


def trunc_file_before_fst_instr(log_file):
    new_lines = []
    with open(log_file, "r") as f:
        lines = f.readlines()
    start = 0
    for i, line in enumerate(lines):
        #print(f"{i} - {line.strip()}")
        if re.search("\[m=example,", line):
            start = i
            break
    with open(log_file, "w") as f:
        f.writelines(lines[start:])

def runLogcatParser(log_file):
    lcp = LogCatParser(log_format="threadtime")
    lcp.parse_file(log_file)
    try:
        test_id = int(os.path.basename(log_file).split("_")[1])
    except:
        test_id = 0
    lcp.save_results(os.path.join(os.path.dirname(log_file), f'test_{test_id}_logresume.json'))


def main(lookup_dir):
   log_files = mega_find(lookup_dir,  pattern="*.logcat", type_file='f', maxdepth=11)
   for lf in log_files:
       #trunc_file_before_fst_instr(lf)
       print(lf)
       runLogcatParser(lf)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("error. provide input dir")