import os
import time

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.AppCrawlerWorkUnit import AppCrawlerWorkUnit

from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.testing_framework.work.WorkUnit import WorkUnit

DEFAULT_RESOURCES_DIR = "resources/testingFrameworks/droidbot"
TEST_OUTPUT_FILENAME = "DROIBOT_RESULT"
DEFAULT_CONFIG_FILE = "droidbot.cfg"
DEFAULT_TEST_SET_SIZE = 10

class DroidBotFramework(AbstractTestingFramework):
    def __init__(self, profiler, default_workload=False, resdir=DEFAULT_RESOURCES_DIR, test_set_size=DEFAULT_TEST_SET_SIZE):
        super(DroidBotFramework, self).__init__(id=TESTING_FRAMEWORK.DROIDBOT, profiler=profiler)
        self.executable_prefix = f"arch -x86_64 python3 {DEFAULT_RESOURCES_DIR}/start.py"
        self.test_set_size = test_set_size
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload()

    def init_default_workload(self, pkg=None):
        self.workload = WorkLoad()
        config = self.__load_config_file()
        for i in range(0, self.test_set_size):
            wk = WorkUnit(self.executable_prefix)
            wk.config(id=None, **config)
            self.workload.add_unit(wk)


    def execute_test(self, apk_path, wunit=None, timeout=None, *args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        out_string = (" -o " + kwargs.get("output_dir")) if "output_dir" in kwargs else ""
        sufix = f"-a {apk_path}{out_string}"
        wunit.execute(sufix, *args, **kwargs)

    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_config_file(self, cfg_filename=None):
        cfg_file = os.path.join(self.res_dir,DEFAULT_CONFIG_FILE) if cfg_filename is None else cfg_filename
        cfg = {}
        ofile = open(cfg_file, "r")
        for aline in ofile:
            key = aline.split("=")[0].strip() if len(aline.split("=")) == 2 else aline.strip()
            pair = aline.split("=")[1].strip() if len(aline.split("=")) == 2 else ""
            cfg["-"+key] = pair
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
            device.clear_logcat()
            self.profiler.stop_profiling()
            self.profiler.export_results(TEST_OUTPUT_FILENAME)
            self.profiler.pull_results(TEST_OUTPUT_FILENAME, app.curr_local_dir)
            app.clean_cache()
            break