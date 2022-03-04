import os
import shutil
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


LOG_FILE = "crawler.out"
DEFAULT_EVENT_COUNT = 1000
TIMEOUT_SECS = 20
CRAWLER_STOP_PHRASE = "Crawl finished"
EXPECTED_OUTPUT_DIR = "crawl_output"


def convert_arg(key, val):
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
    """extends WorkUnit functionality to adapt it to App Crawler framework executions."""
    def __init__(self, bin_cmd, stop_call=None):
        super(AppCrawlerWorkUnit, self).__init__(bin_cmd)
        self.stop_call = stop_call

    def execute(self, package_name, **kwargs):
        #self.__clean_log_file()
        #timeout_cmd = f"gtimeout -s 9 {TIMEOUT_SECS}"
        #self.command = timeout_cmd +" " + self.command % package_name + f" > {LOG_FILE}"
        command = self.command % package_name + f" > {LOG_FILE}"
        print("starting aux thread")
        finish_thread = threading.Thread(target=detect_crawl_finish, args=(True, self.stop_call))
        finish_thread.start()
        print("executing command: " + command)
        res = execute_shell_command(command)
        self.__log_execution_end()

    def config(self, id=None, **kwargs):
        #adb shell monkey -s $monkey_seed -p $package -v --pct-syskeys 0 --ignore-security-exceptions --throttle $delay_bt_events $monkey_nr_events) &> $localDir/monkey$monkey_seed.log)"
        cmd = self.command
        for k, v in kwargs.items():
            cmd += " " + convert_arg(k, v)
        self.command = cmd + " --app-package-name %s "

    def export_results(self, target_dir=None):
        if target_dir is None:
            return
        filepath_log = LOG_FILE
        if os.path.exists(filepath_log):
            target_file = os.path.join(target_dir, filepath_log)
            shutil.move(filepath_log, target_file)
        output_dir = EXPECTED_OUTPUT_DIR
        if os.path.exists(output_dir):
            shutil.move(output_dir, target_dir)

    def __clean_log_file(self):
        execute_shell_command(f"> {LOG_FILE}")

    def __log_execution_end(self):
        execute_shell_command(f"echo \"{CRAWLER_STOP_PHRASE}. timeout\" >> {LOG_FILE}")