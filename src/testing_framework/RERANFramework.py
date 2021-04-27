import os
from sys import path

from src.Types import TESTING_FRAMEWORK
from src.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from src.testing_framework.work.RERANWorkUnit import RERANWorkUnit
from src.testing_framework.work.WorkLoad import WorkLoad
from src.testing_framework.work.WorkUnit import WorkUnit
from src.utils.Utils import mega_find, execute_shell_command

RERAN_RESOURCES_DIR="resources/testingFrameworks/RERAN"
REPLAY_EXECUTABLE_PATH="resources/bin/replay"
REPLAY_EXECUTABLE_NAME="replay"
REPLAY_DEVICE_INSTALL_DIR="/sdcard/RERAN"
RECORDED_TESTS_DIR="resources/testingFrameworks/RERAN/tests"
TESTS_PREFIX = "translated_"

class RERANFramework(AbstractTestingFramework):
    def __init__(self, device, resources_dir=RERAN_RESOURCES_DIR):
        if not device.is_rooted():
            raise Exception("RERAN is not compatible with Non-rooted devices")
        self.device = device
        super(RERANFramework, self).__init__(id=TESTING_FRAMEWORK.RERAN)
        self.workload = None
        self.resources_dir = resources_dir
        if not self.__is_installed():
            self.install()

    def __is_installed(self):
        res = self.device.execute_command("su -c 'ls /data/local/'",shell=True)
        return res.validate(Exception("Error scanning /data/local dir")) and REPLAY_EXECUTABLE_NAME in res.output

    def install(self):
        execute_shell_command(f"{REPLAY_DEVICE_INSTALL_DIR}/build.sh").validate(Exception("Error while builind replay binary"))
        execute_shell_command(f"cd; {REPLAY_DEVICE_INSTALL_DIR}/build ; make").validate(Exception("Error while builind replay binary"))
        execute_shell_command(f"cp {REPLAY_DEVICE_INSTALL_DIR}/build{REPLAY_EXECUTABLE_NAME} {REPLAY_EXECUTABLE_PATH}").validate(
            Exception("Error while builind replay binary"))
        self.device.execute_command(f"mdkir {REPLAY_DEVICE_INSTALL_DIR}", shell=True)
        self.device.execute_command(f"push {REPLAY_EXECUTABLE_PATH} {REPLAY_DEVICE_INSTALL_DIR} ")
        self.device.execute_command(f"su -c \" cp {REPLAY_DEVICE_INSTALL_DIR}/{REPLAY_EXECUTABLE_NAME} /data/local/ \"", shell=True)
        self.device.execute_command(f"su -c \"  chmod 777  /data/local/{REPLAY_EXECUTABLE_NAME}\"",shell=True)

    def load_tests_of_app(self, package_name, reran_tests_dir=RECORDED_TESTS_DIR):
        test_dir = reran_tests_dir + "/" + package_name
        test_files = mega_find(test_dir, pattern="*"+TESTS_PREFIX +"*", type_file='f')
        self.workload = WorkLoad()
        print("loading %d tests" % len(test_files))
        for test_file in test_files:
            print(test_file)
            remote_test_path = self.push_test(test_file)
            wk = RERANWorkUnit(f"su -c \" /data/local/./{REPLAY_EXECUTABLE_NAME} ")
            wk.config(remote_test_path, **{'delay': 0})
            self.workload.add_unit(wk)


    def execute_test(self, package, wunit=None, timeout=None):
        if wunit is None:
            wunit = self.workload.consume()
        wunit.execute(self.device)

    def init(self):
        pass

    def init_default_workload(self, package_name, reran_tests_dir=RECORDED_TESTS_DIR ):
        self.load_tests_of_app(package_name, reran_tests_dir)

    def uninstall(self):
        pass

    def push_test(self, test_path):
        test_basename = os.path.basename(test_path)
        test_remote_path = f"{REPLAY_DEVICE_INSTALL_DIR}/{test_basename}"
        print(test_remote_path)
        self.device.execute_command(f"push {test_path} {test_remote_path} ").validate(Exception("Error while pushing test"))
        return test_remote_path