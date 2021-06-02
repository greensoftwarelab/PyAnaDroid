import os
import time
from sys import path

from src.Types import TESTING_FRAMEWORK
from src.testing_framework.AbstractTestingFramework import AbstractTestingFramework
from src.testing_framework.work.MonkeyRunnerWorkUnit import MonkeyRunnerWorkUnit
from src.testing_framework.work.RERANWorkUnit import RERANWorkUnit
from src.testing_framework.work.WorkLoad import WorkLoad
from src.testing_framework.work.WorkUnit import WorkUnit
from src.utils.Utils import mega_find, execute_shell_command

MONKEY_RUNNER_RESOURCES_DIR="resources/testingFrameworks/monkey-runner"
TESTS_DIR="resources/testingFrameworks/monkey-runner/tests"
MONKEY_RUNNER_BIN_NAME="monkeyrunner"

class MonkeyRunnerFramework(AbstractTestingFramework):
    def __init__(self, default_workload=False, resources_dir=MONKEY_RUNNER_RESOURCES_DIR):
        super(MonkeyRunnerFramework, self).__init__(id=TESTING_FRAMEWORK.MONKEY_RUNNER)
        self.workload = None
        self.resources_dir = resources_dir
        self.__is_installed()
        if default_workload:
            self.init_default_workload()


    def __is_installed(self):
        res = execute_shell_command(f"which {MONKEY_RUNNER_BIN_NAME}")
        return res.validate(Exception("Monkeyrunner not installed. There is probabably an error with your ANDROID SDK installation"))

    def install(self):
       pass

    def load_tests_of_app(self, monkey_tests_dir=TESTS_DIR):
        test_dir = monkey_tests_dir
        test_files = mega_find(test_dir, pattern="*.py", type_file='f')
        self.workload = WorkLoad()
        print("loading %d tests" % len(test_files))
        for test_file in test_files:
            wk = MonkeyRunnerWorkUnit(MONKEY_RUNNER_BIN_NAME)
            wk.config(test_file)
            self.workload.add_unit(wk)


    def execute_test(self, package, wunit=None, timeout=None, *args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        wunit.execute(package, *args, **kwargs)

    def init(self):
        pass

    def init_default_workload(self, tests_dir=TESTS_DIR):
        self.load_tests_of_app(tests_dir)

    def uninstall(self):
        pass

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
            return
