from sys import path

from src.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from src.testing_framework.work.RERANWorkUnit import RERANWorkUnit
from src.testing_framework.work.WorkLoad import WorkLoad
from src.testing_framework.work.WorkUnit import WorkUnit
from src.utils.Utils import mega_find

RERAN_RESOURCES_DIR="resources/testingFrameworks/RERAN"
REPLAY_EXECUTABLE_PATH="resources/bin/replay"
REPLAY_EXECUTABLE_NAME="resources/bin/replay"
REPLAY_DEVICE_INSTALL_DIR="/sdcard/RERAN"
RECORDED_TESTS_DIR="resources/testingFrameworks/RERAN/tests"
TESTS_PREFIX = "translated_"

class RERANFramework(AbstractTestingFramework):
    def __init__(self, device, resources_dir=RERAN_RESOURCES_DIR):
        if not device.is_rooted():
            raise Exception("RERAN is not compatible with Non-rooted device")
        self.device = device
        super(RERANFramework, self).__init__()
        self.workload = None
        self.resources_dir = resources_dir
        if self.__is_installed():
            self.install()


    def __is_installed(self):
        res = self.device.execute_command("adb shell su -c 'ls /data/local/'").validate("Error scanning /data/local dir")
        return REPLAY_EXECUTABLE_NAME in res.output

    def install(self):
        self.device.execute_command(f"mdkir {REPLAY_DEVICE_INSTALL_DIR}", shell=True)
        self.device.execute_command(f"push {REPLAY_EXECUTABLE_PATH} {REPLAY_DEVICE_INSTALL_DIR} ")
        self.device.execute_command(f"su -c \" cp {REPLAY_DEVICE_INSTALL_DIR}/{REPLAY_EXECUTABLE_NAME} /data/local/ \"", shell=True)
        self.device.execute_command(f"su -c \"  chmod 777  /data/local/{REPLAY_EXECUTABLE_NAME}\"",shell=True)

    def load_tests(self,package_name, reran_tests_dir=RECORDED_TESTS_DIR):
        test_dir = reran_tests_dir + "/" + package_name
        test_files = mega_find(test_dir, pattern=TESTS_PREFIX+".*")
        self.workload = WorkLoad()
        for test_file in test_files:
            self.push_test(test_file)
            wk = RERANWorkUnit(f"su -c \" /data/local/./{REPLAY_EXECUTABLE_NAME} ")
            wk.config(test_file, **{'delay':0})
            self.workload.add_unit(wk)


    def execute_test(self, package, wunit=None, timeout=None):
        if wunit is None:
            wunit = self.workload.consume()
        wunit.execute(package)

    def init(self):
        pass

    def uninstall(self):
        pass

    def push_test(self, test_path):
        self.device.execute_command(f"push {test_path} {REPLAY_DEVICE_INSTALL_DIR}/ ").validate("Error while pushing test")
