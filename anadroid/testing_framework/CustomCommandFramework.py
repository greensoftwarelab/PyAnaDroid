import os
import time

from anadroid.Types import TESTING_FRAMEWORK, PROFILER
from anadroid.device.DeviceState import DEVICE_STATE_ENFORCE
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.testing_framework.work.WorkUnit import WorkUnit
from anadroid.utils.Utils import get_resources_dir, loge, logw, logs, execute_shell_command, get_results_dir

DEFAULT_RES_DIR = os.path.join(get_resources_dir(), "testingFrameworks")


class CustomCommandFramework(AbstractTestingFramework):
    """Implements AbstractTestingFramework interface to allow executing tests using an arbitrary command string
    Attributes:
        command(str): command to execute the test
        workload(WorkLoad): workload object containing the work units to be executed..
    """
    def __init__(self, profiler, analyzer, command, default_workload=False, resdir=DEFAULT_RES_DIR):
        super(CustomCommandFramework, self).__init__(id=TESTING_FRAMEWORK.CUSTOM, profiler=profiler, analyzer=analyzer)
        self.command = f'{command} '
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload()

    def init_default_workload(self, pkg=None, unusedarg2=None, tests_dir=None):
        self.workload = WorkLoad()
        max_tests_per_app = self.get_config("tests_per_app", 25)
        for i in range(0, max_tests_per_app):
            wk = WorkUnit(self.command)
            self.workload.add_unit(wk)

    def execute_test(self, package, wunit=None, timeout=None, *args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        if timeout or self.get_config("test_timeout", None):
            timeout_val = timeout if timeout is not None else self.get_config("test_timeout", None)
            wunit.add_timeout(timeout_val)
        if self.profiler.profiler == PROFILER.GREENSCALER:
            cmd = wunit.build_command(package, *args, **kwargs)
            self.profiler.exec_greenscaler(package, cmd)
        else:
            wunit.execute(package, *args, **kwargs)
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}")\
                .validate(Exception("Unable to extract device log"))

    def init(self):
        pass

    def install(self):
        pass

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

    def exec_one_test(self, test_id, device, app, wk_unit, n_retries=1):
        """executes one test identified by test_id of an given app on a given device.
        Args:
            test_id: test uuid.
            device(Device): device.
            app(App): app.
            wk_unit(WorkUnit): work unit to be executed.
            n_retries(int): number of times to try run the test in case it fails.
        """
        if app is None:
            return self.exec_one_test_app_none(test_id, device, wk_unit, n_retries=n_retries)
        if n_retries < 0:
            loge(f"Validation failed. Ignoring test {test_id}")
            return
        device.unlock_screen()
        time.sleep(1)
        device.set_device_state(state_cfg=DEVICE_STATE_ENFORCE.TEST, perm_json=app.get_permissions_json())
        device.save_device_state(filepath=os.path.join(app.curr_local_dir, f'begin_state{test_id}.json'))
        self.profiler.init(**{'app': app})
        log_file = os.path.join(app.curr_local_dir, f"test_{test_id}.logcat")
        # log device state
        self.profiler.start_profiling()
        self.execute_test("", wk_unit, **{'log_filename': log_file})
        self.profiler.stop_profiling()
        # log device state
        device.clear_logcat()
        device.save_device_state(filepath=os.path.join(app.curr_local_dir, f'end_state{test_id}.json'))
        self.profiler.export_results(test_id)
        self.profiler.pull_results(test_id, app.curr_local_dir)
        if not self.analyzer.validate_test(app, test_id, **{'log_filename': log_file}):
            logw("Validation failed. Retrying")
            self.exec_one_test(test_id, device, app, wk_unit, n_retries=n_retries-1)
        else:
            logs(f"Test {test_id} PASSED")

    def exec_one_test_app_none(self, test_id, device, wk_unit, n_retries=1):
        """executes one test identified by test_id on a given device.
        Args:
            test_id: test uuid.
            device(Device): device.
            wk_unit(WorkUnit): work unit to be executed.
            n_retries(int): number of times to try run the test in case it fails.
        """
        test_dir = self.get_default_test_dir()
        if n_retries < 0:
            loge(f"Validation failed. Ignoring test {test_id}")
            return
        if not os.path.exists(test_dir):
            os.mkdir(test_dir)
        device.unlock_screen()
        time.sleep(1)
        device.set_device_state(state_cfg=DEVICE_STATE_ENFORCE.TEST)
        device.save_device_state(filepath=os.path.join(test_dir, f'begin_state{test_id}.json'))
        self.profiler.init()
        log_file = os.path.join(test_dir, f"test_{test_id}.logcat")
        # log device state
        self.profiler.start_profiling()
        self.execute_test("", wk_unit, **{'log_filename': log_file})
        self.profiler.stop_profiling()
        # log device state
        device.clear_logcat()
        device.save_device_state(filepath=os.path.join(test_dir, f'end_state{test_id}.json'))
        self.profiler.export_results(test_id)
        self.profiler.pull_results(test_id, test_dir)
        if not self.analyzer.validate_test(None, test_id, **{'log_filename': log_file}):
            logw("Validation failed. Retrying")
            self.exec_one_test_app_none(test_id, device, wk_unit, n_retries=n_retries-1)
        else:
            logs(f"Test {test_id} PASSED")
