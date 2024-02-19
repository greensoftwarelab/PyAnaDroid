import re
from datetime import datetime
from subprocess import Popen, PIPE, TimeoutExpired
from textops import find
import os
import time
from enum import Enum

from termcolor import colored

DEFAULT_ANALYZERS_FILENAME =  "analyzer_filters.json"

class LogSeverity(Enum):
    SUCCESS = "Success"
    WARNING = "Warning"
    INFO = "Info"
    ERROR = "Error"
    FATAL = "Fatal"


def get_color(sev):
    return {
        'Success': 'green',
        'Warning': 'yellow',
        'Info': 'blue',
        'Error': 'magenta',
        'Fatal': 'red'
    }.get(sev, 'green')


def get_analyzers_filter_file():
    return os.path.join(get_general_config_dir(), DEFAULT_ANALYZERS_FILENAME)\
        if not os.path.exists(DEFAULT_ANALYZERS_FILENAME) else DEFAULT_ANALYZERS_FILENAME


def log(message, log_sev=LogSeverity.INFO, curr_time=None, to_file=True):
    curr_time = time.time() if curr_time is None else curr_time
    color = get_color(log_sev.value)
    adapted_time = re.sub("\s|:", "-", str(datetime.fromtimestamp(curr_time)))
    str_to_print = "[%s] %s: %s" % (log_sev.value, adapted_time, message)
    print(colored(str_to_print, color))
    if to_file:
        log_dir = get_log_dir()
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
        filename = f'{adapted_time}.log'
        f = open(os.path.join(get_log_dir(), filename), "a+")
        f.write(str_to_print+"\n")
        f.close()


def get_log_dir():
    return os.path.join(os.getcwd(), "logs")


def get_reference_dir(packname):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, packname)


def get_resources_dir(packname="anadroid", default_res_dir="resources"):
    ref_dir = get_reference_dir(packname)
    return os.path.join(ref_dir, default_res_dir)


def get_keystore_path():
    return os.path.join(get_resources_dir(), "keys", "pynadroid-releases.keystore")


def get_keystore_pwd():
    return "pynadroid"


def get_general_config_dir(packname="anadroid", default_res_dir="resources"):
    return os.path.join(get_resources_dir(packname, default_res_dir), "config")


def get_pack_dir(packname="anadroid"):
    return get_reference_dir(packname)


def get_results_dir(default_results_dir="anadroid_results"):
    ref_dir = default_results_dir
    if not os.path.exists(ref_dir):
        os.mkdir(ref_dir)
    return ref_dir


def extract_pkg_name_from_apk(apkpath):
    res = execute_shell_command("find $ANDROID_HOME/build-tools/ -name \"aapt\" | sort | tail -1")
    res.validate(Exception("Unable to find aapt executable"))
    aapt_executable = res.output.strip()
    res = execute_shell_command(f"{aapt_executable}  dump badging {apkpath} | grep 'package: name='")
    res.validate(Exception("error while executing aapt"))
    pkg_name = res.output.split(" ")[1].replace("name=", "").replace("'", "")
    return pkg_name


def extract_version_from_apk(apkpath):
    res = execute_shell_command("find $ANDROID_HOME/build-tools/ -name \"aapt\" | sort | tail -1")
    res.validate(Exception("Unable to find aapt executable"))
    aapt_executable = res.output.strip()
    res = execute_shell_command(f"{aapt_executable}  dump badging {apkpath} | grep 'versionName='")
    res.validate(Exception("error while executing aapt"))
    return res.output.split(" ")[3].replace("versionName=", "").replace("'", "")


def get_date_str():
    res = execute_shell_command("date +\"%d_%m_%y_%H_%M_%S\"")
    if res.validate(Exception("Unable to get date")):
        return res.output.strip()


def get_apksigner_bin():
    res = execute_shell_command("find $ANDROID_HOME/build-tools/ -name \"apksigner\" | sort")
    if res.validate(Exception("No apksigner found")):
        return res.output.split()[0]
    return "$ANDROID_HOME/build-tools/30.0.3/apksigner"


def sign_apk(apk_path):
    # deprecated after api 26: "jarsigner -verbose -sigalg SHA2-256withRSA -digestalg SHA2-256
    # -keystore {keystore} {apk_path} {key_alias} <<< \"{passwd}\""
    # .format(keystore=PYNADROID_KEYSTORE_PATH,apk_path=apk_path,key_alias=KEY_ALIAS,passwd=PASSWORD)
    signer_bin = get_apksigner_bin()
    cmd = """{signer_bin} sign --ks {keystore_path} {apk_path} <<< {passwd}""".format(
       signer_bin=signer_bin,
       keystore_path=get_keystore_path(),
       apk_path=apk_path,
       passwd=get_keystore_pwd()
    )
    print(cmd)
    res = execute_shell_command(cmd)
    res.validate("error signing apk " + apk_path)
    return res


def execute_shell_command(cmd, args=(), timeout=None):
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
    return COMMAND_RESULT(proc.returncode, out.decode("utf-8", errors='replace'), err.decode('utf-8', errors='replace'))


def mega_find(basedir, pattern="*", maxdepth=999, mindepth=0, type_file='n'):
    basedir_len = len(basedir.split(os.sep))
    res = find(basedir, pattern=pattern, only_files=type_file == 'f', only_dirs=type_file == 'd')
    # filter by depth
    return list(filter(lambda x: basedir_len + mindepth <= len(x.split(os.sep)) <= maxdepth + basedir_len, res))


class COMMAND_RESULT(object):
    def __init__(self, res, out, err):
        self.return_code = res
        self.output = out
        self.errors = err

    def validate(self, e=None):
        if int(self.return_code) != 0:
            if len(self.errors) > 2:
                if e is None:
                    print(self)
                    return False
                elif isinstance(e, Exception):
                    print(self)
                    raise e
                else:
                    loge(e)
                    print(self)
                    return False
            else:
                #print(self)
                return True
        else:
            return True

    def __str__(self):
        return str(
            {'return_code': self.return_code,
             'output': self.output,
             'errors': self.errors
             })


def log_to_file(content, filename, mode='a+'):
    with open(filename, mode) as u:
        u.write(content + "\n")


def logi(message, to_file=True):
    log(message, log_sev=LogSeverity.INFO, to_file=to_file)


def logw(message, to_file=True):
    log(message, log_sev=LogSeverity.WARNING, to_file=to_file)


def loge(message, to_file=True, exit_on_error=False, error_code=3):
    log(message, log_sev=LogSeverity.ERROR, to_file=to_file)
    if exit_on_error:
        exit(error_code)


def logf(message, to_file=True):
    log(message, log_sev=LogSeverity.FATAL, to_file=to_file)


def logs(message, to_file=True):
    log(message, log_sev=LogSeverity.SUCCESS, to_file=to_file)
