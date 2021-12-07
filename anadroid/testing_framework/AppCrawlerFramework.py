import os
import time

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.AppCrawlerWorkUnit import AppCrawlerWorkUnit

from anadroid.testing_framework.work.WorkLoad import WorkLoad

DEFAULT_RESOURCES_DIR = "resources/testingFrameworks/app-crawler"
DEFAULT_BIN_NAME = "crawl_launcher.jar"
DEFAULT_CONFIG_FILE = "app-crawler.cfg"

DEFAULT_TEST_SET_SIZE = 10

class AppCrawlerFramework(AbstractTestingFramework):
    def __init__(self, profiler, default_workload=False, resdir=DEFAULT_RESOURCES_DIR):
        super(AppCrawlerFramework, self).__init__(id=TESTING_FRAMEWORK.APP_CRAWLER, profiler=profiler)
        self.executable_prefix = f"java -jar {DEFAULT_RESOURCES_DIR}/{DEFAULT_BIN_NAME} "
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload()

    def init_default_workload(self, pkg=None):
        self.workload = WorkLoad()
        config = self.__load_config_file()
        ntests = int(config['test_count']) if 'test_count' in config else DEFAULT_TEST_SET_SIZE
        for i in range(0, ntests):
            wk = AppCrawlerWorkUnit(self.executable_prefix)
            wk.config(id=None, **config)
            self.workload.add_unit(wk)


    def execute_test(self, package, wunit=None, timeout=None,*args, **kwargs):
        # java -jar "$ANADROID_PATH/src/testingFrameworks/app-crawler/crawl_launcher.jar" --apk-file "$installedAPK" --app-package-name "$package"  --android-sdk "$ANDROID_HOME") > "$test_log_file"
        if wunit is None:
            wunit = self.workload.consume()
        wunit.execute(package, *args, **kwargs)

    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_config_file(self, cfg_filename=DEFAULT_CONFIG_FILE ):
        cfg_file = self.res_dir + "/" + cfg_filename
        cfg = {}
        ofile = open(cfg_file, "r")
        for aline in ofile:
            key,pair = aline.split("=")
            cfg[key] = pair.strip()
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
            wk_unit.stop_call = self.profiler.stop_profiling
            log_file = os.path.join(app.curr_local_dir, f"test_{i}.logcat")
            self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
            app.stop()
            self.profiler.export_results("GreendroidResultTrace0.csv")
            self.profiler.pull_results("GreendroidResultTrace0.csv", app.curr_local_dir)
            app.clean_cache()
            break