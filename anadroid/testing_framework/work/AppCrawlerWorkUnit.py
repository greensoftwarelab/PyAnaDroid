import threading
import time

from textops import cat, grep

from anadroid.testing_framework.work.MonkeyWorkUnit import convert_arg
from anadroid.testing_framework.work.WorkUnit import WorkUnit
from anadroid.utils.Utils import execute_shell_command

CRAWLER_OPTIONS = {
    'android-sdk',
    'apk-file',
    'app-package-name',
    'key-store',
    'key-store-password',
    'timeout-sec'
}
CUSTOM_CRAWLER_OPTIONS={
    'test-count'
}


LOG_FILE="crawler.out"
DEFAULT_EVENT_COUNT=1000
TIMEOUT_SECS=20
CRAWLER_STOP_PHRASE="Crawl finished"

def convert_arg(key,val):

    if key in CRAWLER_OPTIONS:
        return "--" + key + " " + val
    elif key in CUSTOM_CRAWLER_OPTIONS:
        return ""
    else:
        print(f"invalid option:-{key}-".format(key=key))
        return ""


def detect_crawl_finish(retry=False, stop_call=None):
    possible_finish = str((cat(LOG_FILE) | grep(CRAWLER_STOP_PHRASE)))
    has_finished = possible_finish is not None and possible_finish != ""
    if not has_finished and retry:
        time.sleep(1)
        detect_crawl_finish(retry=True, stop_call=None)
    if stop_call is not None:
        stop_call()

class AppCrawlerWorkUnit(WorkUnit):
    def __init__(self, bin_cmd, stop_call=None):
        super(AppCrawlerWorkUnit, self).__init__(bin_cmd)
        self.stop_call = stop_call

    def execute(self, package_name, **kwargs):
        self.__clean_log_file()
        timeout_cmd = f"gtimeout -s 9 {TIMEOUT_SECS}"
        self.command = timeout_cmd +" " + self.command % package_name + f" > {LOG_FILE}"
        print("starting aux thread")
        finish_thread = threading.Thread(target=detect_crawl_finish, args=(True, self.stop_call ))
        finish_thread.start()
        print("executing command: " + self.command)
        res = execute_shell_command(self.command)
        self.__log_execution_end()
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}").validate(Exception("Unable to extract device log"))


    def config(self, id=None, **kwargs):
        #adb shell monkey -s $monkey_seed -p $package -v --pct-syskeys 0 --ignore-security-exceptions --throttle $delay_bt_events $monkey_nr_events) &> $localDir/monkey$monkey_seed.log)"
        cmd = self.command
        for k, v in kwargs.items():
            cmd += " " + convert_arg(k, v)
        self.command = cmd + " --app-package-name %s "

    def export_results(self):
        pass

    def __clean_log_file(self):
        execute_shell_command(f"> {LOG_FILE}")

    def __log_execution_end(self):
        execute_shell_command(f"echo \"{CRAWLER_STOP_PHRASE}. timeout\" >> {LOG_FILE}")