import os
import time
from sys import path

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.MonkeyRunnerWorkUnit import MonkeyRunnerWorkUnit
from anadroid.testing_framework.work.RERANWorkUnit import RERANWorkUnit
from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.testing_framework.work.WorkUnit import WorkUnit
from anadroid.utils.Utils import mega_find, execute_shell_command, get_resources_dir, loge, logw, logs

RES_DIR = get_resources_dir()
MONKEY_RUNNER_RESOURCES_DIR = os.path.join(RES_DIR, "testingFrameworks", "monkey-runner")
TESTS_DIR = os.path.join(RES_DIR, "testingFrameworks", "monkey-runner", "tests")
MONKEY_RUNNER_BIN_NAME = "monkeyrunner"


class MonkeyRunnerFramework(AbstractTestingFramework):
    """Implements AbstractTestingFramework interface to allow executing tests using monkeyrunner framework.
    Attributes:
        workload(WorkLoad): workload object containing the work units to be executed.
        resources_dir(str): directory containing app crawler resources.
    """
    def __init__(self, profiler, analyzer, default_workload=False, resources_dir=MONKEY_RUNNER_RESOURCES_DIR):
        super(MonkeyRunnerFramework, self).__init__(id=TESTING_FRAMEWORK.MONKEY_RUNNER,
                                                    profiler=profiler, analyzer=analyzer)
        self.workload = None
        self.resources_dir = resources_dir
        self.__is_installed()
        if default_workload:
            self.init_default_workload(None)

    def __is_installed(self):
        res = execute_shell_command(f"which {MONKEY_RUNNER_BIN_NAME}")
        return res.validate(Exception("Monkeyrunner not installed."
                                      " There is probabably an error with your ANDROID SDK installation"))

    def install(self):
       pass

    def load_tests_of_app(self, monkeyrunner_tests_dir=TESTS_DIR):
        test_dir = TESTS_DIR if monkeyrunner_tests_dir is None else monkeyrunner_tests_dir
        print(f"looking for tests in {test_dir}")
        test_files = mega_find(test_dir, pattern="*.py", type_file='f')
        self.workload = WorkLoad()
        print("loading %d tests" % len(test_files))
        for test_file in test_files:
            wk = MonkeyRunnerWorkUnit(MONKEY_RUNNER_BIN_NAME)
            wk.config(test_file)
            self.workload.add_unit(wk)

    def execute_test(self, package, wunit=None, timeout=None, *args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        if timeout or self.get_config("test_timeout", None):
            timeout_val = timeout if timeout is not None else self.get_config("test_timeout", None)
            wunit.add_timeout(timeout_val)
        wunit.execute(package, *args, **kwargs)
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}").validate(
                Exception("Unable to extract device log"))

    def init(self):
        pass

    def init_default_workload(self, pkg, seeds_file=None, tests_dir=TESTS_DIR):
        self.load_tests_of_app(tests_dir)

    def uninstall(self):
        pass

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
        device.unlock_screen()
        time.sleep(1)
        self.profiler.init(**{'app': app})
        self.profiler.start_profiling()
        app.start()
        log_file = os.path.join(app.curr_local_dir, f"test_{test_id}.logcat")
        self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
        app.stop()
        self.profiler.stop_profiling()
        device.clear_logcat()
        self.profiler.export_results(test_id)
        self.profiler.pull_results(test_id, app.curr_local_dir)
        app.clean_cache()
        if not self.analyzer.validate_test(app, test_id, **{'log_filename': log_file}):
            logw("Validation failed. Retrying")
            self.exec_one_test(test_id, device, app, wk_unit, n_retries=n_retries-1)
        else:
            logs(f"Test {test_id} PASSED ")

