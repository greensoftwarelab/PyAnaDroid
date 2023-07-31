import os
import time

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.AppCrawlerWorkUnit import AppCrawlerWorkUnit
from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.utils.Utils import get_resources_dir, logs, execute_shell_command, logw, loge

DEFAULT_RESOURCES_DIR = os.path.join(get_resources_dir(), "testingFrameworks", "app-crawler")
DEFAULT_BIN_NAME = "crawl_launcher.jar"
DEFAULT_CONFIG_FILE = "app-crawler.cfg"

DEFAULT_TEST_SET_SIZE = 10


class AppCrawlerFramework(AbstractTestingFramework):
    """Implements AbstractTestingFramework interface to allow executing tests using App Crawler.
    Attributes:
        executable_prefix(str): prefix for test command. It is basically a call to java execute the framework's jar.
        workload(WorkLoad): workload object containing the work units to be executed.
        res_dir(str): directory containing app crawler resources.
    """
    def __init__(self, profiler, analyzer, default_workload=False, resdir=DEFAULT_RESOURCES_DIR):
        super(AppCrawlerFramework, self).__init__(id=TESTING_FRAMEWORK.APP_CRAWLER, profiler=profiler, analyzer=analyzer)
        self.executable_prefix = f"java -jar {os.path.join(DEFAULT_RESOURCES_DIR, DEFAULT_BIN_NAME)} "
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload("ignored")

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
        ntests = int(config['test_count']) if 'test_count' in config else DEFAULT_TEST_SET_SIZE
        max_tests_per_app = self.get_config("tests_per_app", 100000000)
        test_lim = max_tests_per_app if max_tests_per_app < ntests else ntests
        for i in range(0, test_lim):
            wk = AppCrawlerWorkUnit(self.executable_prefix)
            wk.config(id=None, **config)
            self.workload.add_unit(wk)

    def execute_test(self, package, wunit=None, timeout=None, *args, **kwargs):
        """execute a test described by a work unit w_unit.
        Args:
            package(str): app package.
            wunit(object): work unit containing information of the test to be executed.
            timeout: test timeout.
        """
        # java -jar "$ANADROID_PATH/src/testingFrameworks/app-crawler/crawl_launcher.jar" --apk-file "$installedAPK" --app-package-name "$package"  --android-sdk "$ANDROID_HOME") > "$test_log_file"
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

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_config_file(self, cfg_filename=DEFAULT_CONFIG_FILE ):
        cfg_file = os.path.join(self.res_dir, cfg_filename) if not os.path.exists(cfg_filename) else cfg_filename
        cfg = {}
        ofile = open(cfg_file, "r")
        for aline in ofile:
            key, pair = aline.split("=")
            cfg[key] = pair.strip()
        ofile.close()
        return cfg

    '''def test_app(self, device, app):
        for i, wk_unit in enumerate(self.workload.work_units):
            device.unlock_screen()
            time.sleep(1)
            self.profiler.init()
            self.profiler.start_profiling()
            app.start()
            time.sleep(8)
            wk_unit.stop_call = self.profiler.stop_profiling
            log_file = os.path.join(app.curr_local_dir, f"test_{i}.logcat")
            self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
            app.stop()
            wk_unit.export_results(app.curr_local_dir)
            self.profiler.export_results("GreendroidResultTrace0.csv")
            self.profiler.pull_results("GreendroidResultTrace0.csv", app.curr_local_dir)
            app.clean_cache()
            break'''

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
        self.profiler.init()
        self.profiler.start_profiling()
        app.start()
        time.sleep(8)
        wk_unit.stop_call = self.profiler.stop_profiling
        log_file = os.path.join(app.curr_local_dir, f"test_{test_id}.logcat")
        self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
        app.stop()
        wk_unit.export_results(app.curr_local_dir)
        self.profiler.export_results(test_id)
        self.profiler.pull_results(test_id, app.curr_local_dir)
        app.clean_cache()
        if not self.analyzer.validate_test(app, test_id, **{'log_filename': log_file}):
            logw("Validation failed. Retrying")
            self.exec_one_test(test_id, device, app, wk_unit, n_retries=n_retries-1)
        else:
            logs(f"Test {test_id} PASSED ")(f"Test {test_id} PASSED ")