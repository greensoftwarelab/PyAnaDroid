from src.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from src.testing_framework.MonkeyWorkUnit import MonkeyWorkUnit
from src.testing_framework.WorkLoad import WorkLoad
import time

from src.testing_framework.WorkUnit import WorkUnit

DEFAULT_RES_DIR = "resources/testingFrameworks/monkey/"
DEFAULT_SEEDS_FILE = "monkey_seeds.txt"
DEFAULT_CONFIG_FILE = "monkey_cmd.cfg"



class MonkeyFramework(AbstractTestingFramework):
    def __init__(self, default_workload=False, resdir=DEFAULT_RES_DIR):
        super(MonkeyFramework, self).__init__()
        self.executable_prefix = "adb shell monkey"
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload(DEFAULT_SEEDS_FILE)

    def init_default_workload(self, seeds_file):
        self.workload = WorkLoad()
        wl_filename = self.res_dir + seeds_file
        config = self.__load_config_file()
        ofile = open(wl_filename, "r")
        for seed in ofile:
            wk = MonkeyWorkUnit(self.executable_prefix)
            wk.config(seed=seed.strip(), **config)
            self.workload.add_unit(wk)
        ofile.close()


    def execute_test(self, package, wunit=None, timeout=None):
        if wunit is None:
            wunit = self.workload.consume()
        wunit.execute(package)

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
            key,pair = aline.split("=")
            cfg[key] = pair.strip()
        ofile.close()
        return cfg