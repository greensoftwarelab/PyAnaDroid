import os
import time

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework

from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.testing_framework.work.WorkUnit import WorkUnit


from anadroid.utils.Utils import get_resources_dir, logs, execute_shell_command, loge, logw

DEFAULT_RESOURCES_DIR = os.path.join(get_resources_dir(), "testingFramework", "junit")


class JUnitBasedFramework(AbstractTestingFramework):
    """Implements AbstractTestingFramework interface to allow executing tests using JUnit based testing frameworks.
    The tests executed are barely configurable. This class lists instrumentations on device and runs one by one.
    Attributes:
        executable_prefix(str): prefix for test command. It is basically a call to the executable.
        workload(WorkLoad): workload object containing the work units to be executed.
        res_dir(str): directory containing app crawler resources.
    """
    def __init__(self, profiler, analyzer, resdir=DEFAULT_RESOURCES_DIR):
        super(JUnitBasedFramework, self).__init__(id=TESTING_FRAMEWORK.JUNIT, profiler=profiler, analyzer=analyzer)
        self.executable_prefix = "adb shell am instrument -w "
        self.workload = None
        self.res_dir = resdir

    def init_default_workload(self, pkg, seeds_file=None, tests_dir=None):
        pass

    def execute_test(self, package, wunit=None, timeout=None, *args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        if timeout or self.get_config("test_timeout", None):
            timeout_val = timeout if timeout is not None else self.get_config("test_timeout", None)
            wunit.add_timeout(timeout_val)
        wunit.execute("", *args, **kwargs)
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}").validate(
                Exception("Unable to extract device log"))

    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_available_instrumentations(self, device, pkg):
        l = []
        res = device.execute_command(f"pm list instrumentation | grep {pkg} | cut -f2 -d: | cut -f1 -d\ ", shell=True)
        if res.validate(Exception("Unable to obtain instrumentations for package x")) and len(res.output) > 5:
            for s in res.output.split():
                l.append(s)
        return l

    def __load_app_workload(self, device, pkg):
        """loads instrumentations of app package and configures workload accordingly.
        Args:
            device(Device): device.
            pkg: app package.
        """
        self.workload = WorkLoad()
        instrumentations = self.__load_available_instrumentations(device, pkg)
        max_tests_per_app = self.get_config("tests_per_app", 100000000)
        i = 0
        for x in instrumentations:
            if i >= max_tests_per_app:
                logw(f"number of tests limited by tests_per_app. Considering {max_tests_per_app} tests per app")
            wk = WorkUnit(self.executable_prefix)
            wk.config(x)
            print(wk.command)
            self.workload.add_unit(wk)
            i = i+1

    def test_app(self, device, app):
        """test a given app on a given device.
        Executes each work unit of workload on app running on device.
        Args:
            device(Device): device.
            app(App): app.
        """
        self.__load_app_workload(device, app.package_name)
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
        self.profiler.init()
        self.profiler.start_profiling()
        # app.start()
        time.sleep(3)
        print(wk_unit)
        log_file = os.path.join(app.curr_local_dir, f"test_{test_id}.logcat")
        self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
        # app.stop()
        self.profiler.stop_profiling()
        self.profiler.export_results(test_id)
        self.profiler.pull_results(test_id, app.curr_local_dir)
        app.clean_cache()
        device.clear_logcat()
        if not self.analyzer.validate_test(app, test_id, **{'log_filename': log_file}):
            logw("Validation failed. Retrying")
            self.exec_one_test(test_id, device, app, wk_unit, n_retries=n_retries-1)
        else:
            logs(f"Test {test_id} PASSED ")
