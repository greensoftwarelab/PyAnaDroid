import os
import time

from anadroid.Types import TESTING_FRAMEWORK, PROFILER
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.MonkeyWorkUnit import MonkeyWorkUnit
from anadroid.testing_framework.work.WorkLoad import WorkLoad

DEFAULT_RES_DIR = "resources/testingFrameworks/monkey/"
DEFAULT_SEEDS_FILE = "monkey_seeds.txt"
DEFAULT_CONFIG_FILE = "monkey_cmd.cfg"



class MonkeyFramework(AbstractTestingFramework):
    def __init__(self, profiler, default_workload=False, resdir=DEFAULT_RES_DIR):
        super(MonkeyFramework, self).__init__(id=TESTING_FRAMEWORK.MONKEY, profiler=profiler)
        self.executable_prefix = "adb shell monkey"
        self.workload = None
        self.res_dir = resdir
        if default_workload:
            self.init_default_workload(DEFAULT_SEEDS_FILE)

    def init_default_workload(self, pkg, seeds_file=DEFAULT_SEEDS_FILE):
        self.workload = WorkLoad()
        wl_filename = os.path.join(self.res_dir, seeds_file)
        config = self.__load_config_file()
        ofile = open(wl_filename, "r")
        for seed in ofile:
            wk = MonkeyWorkUnit(self.executable_prefix)
            wk.config(seed=seed.strip(), **config)
            self.workload.add_unit(wk)
        ofile.close()

    def execute_test(self, package, wunit=None, timeout=None, *args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        if self.profiler.profiler == PROFILER.GREENSCALER:
            cmd = wunit.build_command(package, *args, **kwargs)
            self.profiler.exec_greenscaler(package, cmd)
        else:
            wunit.execute(package, *args, **kwargs)

    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_config_file(self, cfg_filename=DEFAULT_CONFIG_FILE):
        cfg_file = self.res_dir + cfg_filename
        cfg = {}
        ofile = open(cfg_file, "r")
        for aline in ofile:
            key, pair = aline.split("=")
            cfg[key] = pair.strip()
        ofile.close()
        return cfg

    def test_app(self, device, app):
        j = 0
        for i, wk_unit in enumerate(self.workload.work_units):
            device.unlock_screen()
            time.sleep(1)
            self.profiler.init(**{'app': app})
            self.profiler.start_profiling()
            app.start()
            log_file = os.path.join(app.curr_local_dir, f"test_{i}.logcat")
            self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
            app.stop()
            self.profiler.stop_profiling()
            device.clear_logcat()
            self.profiler.export_results(f"GreendroidResultTrace{i}.csv")
            self.profiler.pull_results(f"GreendroidResultTrace{i}.csv", app.curr_local_dir)
            app.clean_cache()
            break