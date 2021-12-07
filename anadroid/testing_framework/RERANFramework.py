import os
import time
from sys import path

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from anadroid.testing_framework.work.RERANWorkUnit import RERANWorkUnit
from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.testing_framework.work.WorkUnit import WorkUnit
from anadroid.utils.Utils import mega_find, execute_shell_command
from resources.testingFrameworks.RERAN.src.RERANWrapper import RERANWrapper

RERAN_RESOURCES_DIR = "resources/testingFrameworks/RERAN"
TRANSLATOR_JAR_PATH="resources/testingFrameworks/RERAN/build/RERANTranslate.jar"
RERAN_CONFIG_FILE = "config.cfg"
DEFAULT_REPLAY_EXECUTABLE_PATH = "resources/testingFrameworks/RERAN/build/replay"
DEFAULT_REPLAY_EXECUTABLE_NAME = "replay"
DEFAULT_REPLAY_DEVICE_INSTALL_DIR = "/sdcard/RERAN"
DEFAULT_RECORDED_TESTS_DIR = "resources/testingFrameworks/RERAN/tests"
DEFAULT_TESTS_PREFIX = "translated_"




class RERANFramework(AbstractTestingFramework):


    def __init__(self, device, profiler, resources_dir=RERAN_RESOURCES_DIR):
        if not device.is_rooted():
            raise Exception("RERAN is not compatible with Non-rooted devices")
        self.device = device
        self.resources_dir = resources_dir
        super(RERANFramework, self).__init__(id=TESTING_FRAMEWORK.RERAN,profiler=profiler)
        self.workload = None
        self.config = self.__load_config()
        if not self.__is_installed():
            self.install()

    def __load_config(self):
        cfg_file = os.path.join(self.resources_dir, "config.cfg")
        cfg = {}
        ofile = open(cfg_file, "r")
        for aline in ofile:
            key, pair = aline.split("=")
            cfg[key] = pair.strip()
        ofile.close()
        return cfg

    def __get_config(self,key):
        val = None
        if key in self.config:
            val = self.config[key]
        elif key in globals():
            val = globals()[key]
        return val


    def __is_installed(self):
        res = self.device.execute_command("su -c 'ls /data/local/'",shell=True)
        return res.validate() and self.__get_config("REPLAY_EXECUTABLE_NAME") in res.output

    def install(self):
        local_dir =  self.__get_config("RERAN_RESOURCES_DIR")
        device_install_dir = self.__get_config("REPLAY_DEVICE_INSTALL_DIR")
        bin_name = self.__get_config("REPLAY_EXECUTABLE_NAME")
        bin_path =  self.__get_config("REPLAY_EXECUTABLE_PATH")
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
        print("rerun" + reran_tests_dir)
        test_dir = os.path.join(reran_tests_dir , package_name)
        prefix = self.__get_config("TESTS_PREFIX")
        test_files = mega_find(test_dir, pattern=f"*{prefix}*", type_file='f')
        self.workload = WorkLoad()
        print("loading %d tests" % len(test_files))
        bin_name = self.__get_config("REPLAY_EXECUTABLE_NAME")
        for test_file in test_files:
            print(test_file)
            remote_test_path = self.push_test(test_file)
            wk = RERANWorkUnit(f"su -c \" /data/local/./{bin_name} ")
            wk.config(remote_test_path, **{'delay': 0})
            self.workload.add_unit(wk)


    def execute_test(self, package, wunit=None, timeout=None,*args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()

        wunit.execute(self.device, *args, **kwargs)


    def init(self):
        pass

    def init_default_workload(self, package_name, reran_tests_dir=None ):
        self.load_tests_of_app(package_name, reran_tests_dir)

    def uninstall(self):
        pass

    def push_test(self, test_path):
        test_basename = os.path.basename(test_path)
        dev_install_dir = self.__get_config("REPLAY_DEVICE_INSTALL_DIR")
        test_remote_path = f"{dev_install_dir}/{test_basename}"
        self.device.execute_command(f"push {test_path} {test_remote_path} ").validate(Exception("Error while pushing test"))
        return test_remote_path

    def test_app(self, device, app):
        for i, wk_unit in enumerate(self.workload.work_units):
            device.unlock_screen()
            time.sleep(1)
            self.profiler.init()
            self.profiler.start_profiling()
            app.start()
            time.sleep(1)
            log_file = os.path.join(app.curr_local_dir, f"test_{i}.logcat")
            self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
            app.stop()
            self.profiler.stop_profiling()
            self.profiler.export_results("GreendroidResultTrace0.csv")
            self.profiler.pull_results("GreendroidResultTrace0.csv", app.curr_local_dir)
            app.clean_cache()
            return

    def is_recordable(self):
        return True

    def record_test(self, app_id=None, test_id=None):
        if test_id is None:
            test_id = f'{time.time()}'
        if app_id is None:
            app_id = "unknown"
        r = RERANWrapper(DEFAULT_RECORDED_TESTS_DIR, TRANSLATOR_JAR_PATH, DEFAULT_REPLAY_EXECUTABLE_PATH)
        out_file = r.record(app_id, test_id)
        print(f"recorded test: {out_file}")
        return out_file