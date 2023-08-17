import os
import time

from anadroid.Types import TESTING_FRAMEWORK, PROFILER
from anadroid.device.DeviceState import DEVICE_STATE_ENFORCE
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.MonkeyWorkUnit import MonkeyWorkUnit
from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.utils.Utils import get_resources_dir, loge, logw, logs, execute_shell_command, logi

#DEFAULT_RES_DIR = "resources/testingFrameworks/monkey/"
DEFAULT_RES_DIR = os.path.join(get_resources_dir(), "testingFrameworks", "monkey")
DEFAULT_SEEDS_FILE = "monkey_seeds.txt"
DEFAULT_CONFIG_FILE = "monkey.cfg"


class MonkeyFramework(AbstractTestingFramework):
    """Implements AbstractTestingFramework interface to allow executing tests using Monkey testing framework.
    Attributes:
        executable_prefix(str): prefix for test command. It is basically a call to the executable.
        workload(WorkLoad): workload object containing the work units to be executed.
        res_dir(str): directory containing app crawler resources.
    """
    def __init__(self, profiler, analyzer, default_workload=False, resdir=DEFAULT_RES_DIR):
        super(MonkeyFramework, self).__init__(id=TESTING_FRAMEWORK.MONKEY, profiler=profiler, analyzer=analyzer)
        self.executable_prefix = "adb shell monkey"
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload(DEFAULT_SEEDS_FILE)

    def init_default_workload(self, pkg, seeds_file=DEFAULT_SEEDS_FILE, tests_dir=None):
        self.workload = WorkLoad()
        config = self.__load_config_file()
        ofile = open(os.path.join(self.res_dir, seeds_file), "r")
        max_tests_per_app = self.get_config("tests_per_app", 100000000)
        for i, seed in enumerate(ofile):
            if i >= max_tests_per_app:
                break
            wk = MonkeyWorkUnit(self.executable_prefix)
            wk.config(seed=seed.strip(), **config)
            self.workload.add_unit(wk)
        ofile.close()

    def execute_test(self, package, w_unit=None, timeout=None, *args, **kwargs):
        if w_unit is None:
            w_unit = self.workload.consume()
        if timeout or self.get_config("test_timeout", None):
            timeout_val = timeout if timeout is not None else self.get_config("test_timeout", None)
            w_unit.add_timeout(timeout_val)
        if self.profiler.profiler == PROFILER.GREENSCALER:
            cmd = w_unit.build_command(package, *args, **kwargs)
            self.profiler.exec_greenscaler(package, cmd)
        else:
            w_unit.execute(package, *args, **kwargs)
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}").validate(Exception("Unable to extract device log"))

    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_config_file(self, cfg_filename=DEFAULT_CONFIG_FILE):
        cfg_file = os.path.join(self.res_dir, cfg_filename) if not os.path.exists(cfg_filename) else cfg_filename
        logi(f"Monkey Testing Framework: Loading config file: {cfg_file}")
        cfg = {}
        ofile = open(cfg_file, "r")
        for aline in ofile:
            key, pair = aline.split("=")
            cfg[key] = pair.strip()
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
        device.set_device_state(state_cfg=DEVICE_STATE_ENFORCE.TEST, perm_json=app.get_permissions_json())
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
        app.start()
        self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
        app.stop()
        self.profiler.stop_profiling()
        # log device state
        device.clear_logcat()
        device.save_device_state(filepath=os.path.join(app.curr_local_dir, f'end_state{test_id}.json'))
        self.profiler.export_results(test_id)
        self.profiler.pull_results(test_id, app.curr_local_dir)
        app.clean_cache()
        device.set_device_state(state_cfg=DEVICE_STATE_ENFORCE.TEST, perm_json=app.get_permissions_json())
        if not self.analyzer.validate_test(app, test_id, **{'log_filename': log_file}):
            logw("Validation failed. Retrying")
            self.exec_one_test(test_id, device, app, wk_unit, n_retries=n_retries-1)
        else:
            logs(f"Test {test_id} PASSED")
