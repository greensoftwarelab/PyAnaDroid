import os
import time

from src.Types import TESTING_FRAMEWORK
from src.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from src.testing_framework.work.MonkeyWorkUnit import MonkeyWorkUnit
from src.testing_framework.work.WorkLoad import WorkLoad

DEFAULT_RES_DIR = "resources/testingFrameworks/monkey/"
DEFAULT_SEEDS_FILE = "monkey_seeds.txt"
DEFAULT_CONFIG_FILE = "monkey_cmd.cfg"



class MonkeyFramework(AbstractTestingFramework):
    def __init__(self, default_workload=False, resdir=DEFAULT_RES_DIR):
        super(MonkeyFramework, self).__init__(id=TESTING_FRAMEWORK.MONKEY)
        self.executable_prefix = "adb shell monkey"
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload(DEFAULT_SEEDS_FILE)

    def init_default_workload(self, pkg , seeds_file=DEFAULT_SEEDS_FILE):
        self.workload = WorkLoad()
        wl_filename = os.path.join(self.res_dir, seeds_file)
        config = self.__load_config_file()
        ofile = open(wl_filename, "r")
        for seed in ofile:
            wk = MonkeyWorkUnit(self.executable_prefix)
            wk.config(seed=seed.strip(), **config)
            self.workload.add_unit(wk)
        ofile.close()


    def execute_test(self, package, wunit=None, timeout=None,*args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        wunit.execute(package, args, kwargs)

    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_config_file(self, cfg_filename=DEFAULT_CONFIG_FILE ):
        cfg_file = self.res_dir + cfg_filename
        cfg = {}
        ofile = open(cfg_file, "r")
        for aline in ofile:
            key, pair = aline.split("=")
            cfg[key] = pair.strip()
        ofile.close()
        return cfg

    def test_app(self, device, app, profiler):
        for wk_unit in self.workload.work_units:
            device.unlock_screen()
            time.sleep(1)
            profiler.init()
            profiler.start_profiling()
            app.start()
            time.sleep(1)
            self.execute_test(app.package_name, wk_unit)
            app.stop()
            profiler.stop_profiling()
            profiler.export_results("GreendroidResultTrace0.csv")
            profiler.pull_results("GreendroidResultTrace0.csv", app.curr_local_dir)
            app.clean_cache()
            break