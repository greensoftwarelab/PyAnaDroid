import os
import time

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.RERANWorkUnit import RERANWorkUnit
from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.utils.Utils import mega_find, execute_shell_command, get_resources_dir, loge, logw, logi, logs
from anadroid.resources.testingFrameworks.reran.src.RERANWrapper import RERANWrapper

RERAN_RESOURCES_DIR = os.path.join(get_resources_dir(), "testingFrameworks", "RERAN")
TRANSLATOR_JAR_PATH = os.path.join(RERAN_RESOURCES_DIR, "build", "RERANTranslate.jar")
RERAN_CONFIG_FILE = "reran.cfg"
REPLAY_EXECUTABLE_PATH = os.path.join(RERAN_RESOURCES_DIR, "build", "replay")
REPLAY_EXECUTABLE_NAME = "replay"
REPLAY_DEVICE_INSTALL_DIR = "/sdcard/RERAN"
RECORDED_TESTS_DIR = os.path.join(RERAN_RESOURCES_DIR, "tests")
TESTS_PREFIX = "translated_"


class RERANFramework(AbstractTestingFramework):
    """Implements AbstractTestingFramework interface to allow recording and executing tests using RERAN framework.
    Attributes:
        workload(WorkLoad): workload object containing the work units to be executed.
        resources_dir(str): directory containing app crawler resources.
    """
    def __init__(self, device, profiler, analyzer, resources_dir=RERAN_RESOURCES_DIR):
        if not device.is_rooted():
            raise Exception("RERAN is not compatible with Non-rooted devices")
        self.device = device
        self.resources_dir = resources_dir
        super(RERANFramework, self).__init__(id=TESTING_FRAMEWORK.RERAN, profiler=profiler, analyzer=analyzer)
        self.workload = None
        self.config = self.__load_config()
        if not self.__is_installed():
            self.install()

    def __load_config(self):
        cfg_file = os.path.join(self.resources_dir, RERAN_CONFIG_FILE) \
            if not os.path.exists(RERAN_CONFIG_FILE) else RERAN_CONFIG_FILE
        cfg = {}
        if os.path.exists(cfg_file):
            ofile = open(cfg_file, "r")
            for aline in ofile:
                x = aline.split("=")
                if len(x) > 1:
                    key, pair = aline.split("=")
                    cfg[key] = pair.strip()
            ofile.close()
        return cfg

    def __get_config(self, key):
        val = None
        if key in self.config:
            val = self.config[key]
        elif key in globals():
            val = globals()[key]
        return val


    def __is_installed(self):
        res = self.device.execute_command("su -c 'ls /data/local/'", shell=True)
        return res.validate() and self.__get_config("REPLAY_EXECUTABLE_NAME") in res.output

    def install(self):
        local_dir = self.__get_config("RERAN_RESOURCES_DIR")
        device_install_dir = self.__get_config("REPLAY_DEVICE_INSTALL_DIR")
        bin_name = self.__get_config("REPLAY_EXECUTABLE_NAME")
        bin_path = self.__get_config("REPLAY_EXECUTABLE_PATH")
        execute_shell_command(f"cd {local_dir} ; ./build.sh").validate(Exception("Error while building replay binary"))
        execute_shell_command(f"cd {local_dir}/build ; make").validate(Exception("Error while building replay binary"))
        execute_shell_command(f"cp {local_dir}/build/{bin_name} {bin_path}").validate(
            Exception("Error while building replay binary"))
        self.device.execute_command(f"mdkir {device_install_dir}", shell=True)
        self.device.execute_command(f"push {bin_path} {device_install_dir} ")
        self.device.execute_command(f"su -c \" cp {device_install_dir}/{bin_name} /data/local/ \"", shell=True)
        self.device.execute_command(f"su -c \"  chmod 777  /data/local/{bin_name}\"",shell=True)

    def load_tests_of_app(self, package_name, reran_tests_dir=None):
        reran_tests_dir = reran_tests_dir if reran_tests_dir is not None else self.__get_config("RECORDED_TESTS_DIR")
        test_dir = reran_tests_dir # os.path.join(reran_tests_dir, package_name)
        prefix = self.__get_config("TESTS_PREFIX")
        logi(f"searching for tests in {test_dir}")
        test_files = mega_find(test_dir, pattern=f"*{prefix}*", type_file='f')
        self.workload = WorkLoad()
        print("loading %d tests" % len(test_files))
        bin_name = self.__get_config("REPLAY_EXECUTABLE_NAME")
        max_tests_per_app = self.get_config("tests_per_app", 100000000)
        i = 0
        for test_file in test_files:
            if i >= max_tests_per_app:
                break
            remote_test_path = self.push_test(test_file)
            wk = RERANWorkUnit(f"su -c \" /data/local/./{bin_name} ")
            wk.config(remote_test_path, **{'delay': 0})
            self.workload.add_unit(wk)
            i += 1

    def execute_test(self, package, wunit=None, timeout=None,*args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        if timeout or self.get_config("test_timeout", None):
            timeout_val = timeout if timeout is not None else self.get_config("test_timeout", None)
            wunit.add_timeout(timeout_val)
        wunit.execute(self.device, *args, **kwargs)
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}").validate(
                Exception("Unable to extract device log"))

    def init(self):
        pass

    def init_default_workload(self, pkg, seeds_file=None, tests_dir=None):
        self.load_tests_of_app(pkg, tests_dir)

    def uninstall(self):
        pass

    def push_test(self, test_path):
        """push test to device."""
        test_basename = os.path.basename(test_path)
        dev_install_dir = self.__get_config("REPLAY_DEVICE_INSTALL_DIR")
        test_remote_path = f"{dev_install_dir}/{test_basename}"
        self.device.execute_command(f"push {test_path} {test_remote_path} ").validate(Exception("Error while pushing test"))
        return test_remote_path

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

    def is_recordable(self):
        """checks if framework can record tests."""
        return True

    def record_test(self, app_id=None, test_id=None, output_dir=None):
        """record test of a given app, identified by test_id."""
        if test_id is None:
            test_id = f'{time.time()}'
        if app_id is None:
            app_id = "unknown"
        # tests_folder, translator_jar_path, replay_bin_path):
        tdir = output_dir if output_dir is not None else RECORDED_TESTS_DIR
        r = RERANWrapper(tdir, TRANSLATOR_JAR_PATH, REPLAY_EXECUTABLE_PATH)
        out_file = r.record(app_id, test_id)
        print(f"recorded test: {out_file}")
        return out_file