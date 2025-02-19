import os
import time

from anadroid.Config import get_general_config
from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.AppCrawlerWorkUnit import AppCrawlerWorkUnit
from anadroid.testing_framework.work.DroidBotWorkUnit import DroidBotWorkUnit
from anadroid.utils.Utils import mega_find, execute_shell_command, get_resources_dir, loge, logw, logs, logi
from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.testing_framework.work.WorkUnit import WorkUnit


DROIDBOT_RESOURCES_DIR = os.path.join(get_resources_dir(), "testingFrameworks", "droidbot")
TEST_OUTPUT_FILENAME = "DROIBOT_RESULT"
DEFAULT_CONFIG_FILE = "droidbot.cfg"


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
    """Implements AbstractTestingFramework interface to allow executing tests using DroidBot.
    Attributes:
        executable_prefix(str): prefix for test command. It is basically a call to the executable.
        workload(WorkLoad): workload object containing the work units to be executed.
        res_dir(str): directory containing app crawler resources.
    """
    def __init__(self, profiler, analyzer, default_workload=False, resdir=DROIDBOT_RESOURCES_DIR):
        super(DroidBotFramework, self).__init__(id=TESTING_FRAMEWORK.DROIDBOT, profiler=profiler, analyzer=analyzer)
        exec_prefix = get_general_config("general")['commands_prefix'] if \
            'commands_prefix' in get_general_config("general") else " "
        self.executable_prefix = f'{exec_prefix} python3 {os.path.join(resdir,"start.py")}'
        print(self.executable_prefix)
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload("")

    def init_default_workload(self, pkg, args_file=None, tests_dir=None):
        """Initializes the workload with AppCrawlerWorkUnits.
        Initializes workload attribute with many AppCrawlerWorkUnits, configured with configurations
        coming from config file.
        Args:
            pkg: app package (ignored).
            args_file: ignored.
            tests_dir: ignored.
        """
        self.workload = WorkLoad()
        config = self.__load_config_file()
        max_tests_per_app = self.get_config("tests_per_app", 20)
        for i in range(0, max_tests_per_app):
            wk = DroidBotWorkUnit(self.executable_prefix)
            wk.config(id=None, **config)
            self.workload.add_unit(wk)

    def execute_test(self, apk_path, wunit=None, timeout=None, *args, **kwargs):
        """execute a test described by a work unit w_unit.
        Args:
            package(str): app package.
            wunit(object): work unit containing information of the test to be executed.
            timeout: test timeout.
        """
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
        if cfg_filename is None:
            cfg_filename = DEFAULT_CONFIG_FILE
        cfg_file = os.path.join(self.res_dir, cfg_filename) if not os.path.exists(cfg_filename) else cfg_filename
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
        """test a given app on a given device.
        Executes each work unit of workload on app running on device.
        Args:
            device(Device): device.
            app(App): app.
        """
        retries_per_test = self.get_config("test_fail_retries", 1)
        for i, wk_unit in enumerate(self.workload.work_units):
            self.exec_one_test(i, device, app, wk_unit, n_retries=retries_per_test)


    def exec_one_test(self, test_id, device, app,  wk_unit, n_retries=1):
        """executes one test identified by test_id of an given app on a given device.
        Args:
            test_id: test uuid.
            device(Device): device.
            app(App): app.
            wk_unit(WorkUnit): work unit to be executed.
            n_retries(int): number of times to try run the test in case it fails.
        """
        if n_retries < 0:
            loge(f"Validation failed. Ignoring test {test_id}")
            return
        logi(f"Executing test {test_id}")
        device.unlock_screen()
        time.sleep(1)
        self.profiler.init()
        self.profiler.start_profiling()
        app.start()
        time.sleep(10)
        log_file = os.path.join(app.curr_local_dir, f"test_{test_id}.logcat")
        self.execute_test(app.apk, wk_unit, **{'log_filename': log_file, 'output_dir': app.curr_local_dir})
        app.stop()
        self.profiler.stop_profiling()
        device.clear_logcat()
        self.profiler.export_results(TEST_OUTPUT_FILENAME)
        self.profiler.pull_results(test_id, app.curr_local_dir)
        app.clean_cache()
        if not self.analyzer.validate_test(app, test_id, **{'log_filename': log_file}):
            logw("Validation failed. Retrying")
            self.exec_one_test(test_id, device, app, wk_unit, n_retries=n_retries-1)
        else:
            logs(f"Test {test_id} PASSED ")
