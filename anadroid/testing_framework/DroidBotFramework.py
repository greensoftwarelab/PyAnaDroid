import os
import time

from anadroid.Config import get_general_config
from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.AppCrawlerWorkUnit import AppCrawlerWorkUnit
from anadroid.testing_framework.work.DroidBotWorkUnit import DroidBotWorkUnit
from anadroid.utils.Utils import mega_find, execute_shell_command, get_resources_dir
from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.testing_framework.work.WorkUnit import WorkUnit


DROIDBOT_RESOURCES_DIR = os.path.join(get_resources_dir(), "testingFrameworks", "droidbot")
TEST_OUTPUT_FILENAME = "DROIBOT_RESULT"
DEFAULT_CONFIG_FILE = "droidbot_cmd.cfg"

def get_machine_arch():
    res = execute_shell_command("uname -m")
    if res.validate("unable to detect system arch"):
        return res.output.strip()
    return ""


def get_exec_prefix():
    machine_arc = get_machine_arch()
    if "arm64" in machine_arc:
        return "arch -x86_64"
    # todo uncomment
    return ""
    #return "arch -x86_64"


class DroidBotFramework(AbstractTestingFramework):
    def __init__(self, profiler, analyzer, default_workload=False, resdir=DROIDBOT_RESOURCES_DIR):
        super(DroidBotFramework, self).__init__(id=TESTING_FRAMEWORK.DROIDBOT, profiler=profiler, analyzer=analyzer)
        exec_prefix = get_general_config("general")['commands_prefix'] if \
            'commands_prefix' in get_general_config("general") else " "
        self.executable_prefix = f'{exec_prefix} python3 {os.path.join(resdir,"start.py")}'
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload()

    def init_default_workload(self, pkg, seeds_file=None, tests_dir=None):
        self.workload = WorkLoad()
        config = self.__load_config_file()
        max_tests_per_app = self.get_config("tests_per_app", 20)
        for i in range(0, max_tests_per_app):
            wk = DroidBotWorkUnit(self.executable_prefix)
            wk.config(id=None, **config)
            self.workload.add_unit(wk)


    def execute_test(self, apk_path, wunit=None, timeout=None, *args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        if timeout or self.get_config("test_timeout", None):
            timeout_val = timeout if timeout is not None else self.get_config("test_timeout", None)
            wunit.add_timeout(timeout_val)
        out_string = (" -o " + kwargs.get("output_dir")) if "output_dir" in kwargs else ""
        suffix = f"-a {apk_path}{out_string}"
        wunit.execute(suffix, *args, **kwargs)
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}").validate(
                Exception("Unable to extract device log"))

    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_config_file(self, cfg_filename=None):
        cfg_file = os.path.join(self.res_dir, DEFAULT_CONFIG_FILE) if cfg_filename is None else cfg_filename
        cfg = {}
        if os.path.exists(cfg_file):
            ofile = open(cfg_file, "r")
            for aline in ofile:
                key = aline.split("=")[0].strip() if len(aline.split("=")) == 2 else aline.strip()
                pair = aline.split("=")[1].strip() if len(aline.split("=")) == 2 else ""
                cfg[key] = pair
            ofile.close()
        return cfg

    def test_app(self, device, app):
        for i, wk_unit in enumerate(self.workload.work_units):
            device.unlock_screen()
            time.sleep(1)
            self.profiler.init()
            self.profiler.start_profiling()
            app.start()
            time.sleep(10)
            log_file = os.path.join(app.curr_local_dir, f"test_{i}.logcat")
            self.execute_test(app.apk, wk_unit, **{'log_filename': log_file, 'output_dir': app.curr_local_dir})
            app.stop()
            self.profiler.stop_profiling()
            device.clear_logcat()
            self.profiler.export_results(TEST_OUTPUT_FILENAME)
            self.profiler.pull_results(TEST_OUTPUT_FILENAME, app.curr_local_dir)
            app.clean_cache()