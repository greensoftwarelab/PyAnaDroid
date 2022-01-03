import os
import time

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.testing_framework.AbstractTestingFramework import AbstractTestingFramework

from anadroid.testing_framework.work.WorkLoad import WorkLoad
from anadroid.testing_framework.work.WorkUnit import WorkUnit

DEFAULT_RESOURCES_DIR="resources/testingFramework/junit"


class JUnitBasedFramework(AbstractTestingFramework):
    def __init__(self, profiler, resdir=DEFAULT_RESOURCES_DIR):
        super(JUnitBasedFramework, self).__init__(id=TESTING_FRAMEWORK.JUNIT, profiler=profiler)
        self.executable_prefix = "adb shell am instrument -w "
        self.workload = None
        self.res_dir = resdir

    def init_default_workload(self, pkg):
        pass


    def execute_test(self, package, wunit=None, timeout=None,*args, **kwargs):
        if wunit is None:
            wunit = self.workload.consume()
        wunit.execute("", *args, **kwargs)


    def init(self):
        pass

    def install(self):
        pass

    def uninstall(self):
        pass

    def __load_available_instrumentations(self, device, pkg):
        l = []
        res = device.execute_command(f"pm list instrumentation | grep {pkg} | cut -f2 -d: | cut -f1 -d\ ", shell=True)
        if res.validate(Exception("Unable to obtain instrumentations for package x")) and len(res.output) > 5:
            for s in res.output.split():
                l.append(s)
        return l


    def __load_app_workload(self, device, pkg):
        self.workload = WorkLoad()
        instrumentations = self.__load_available_instrumentations(device, pkg)
        for x in instrumentations:
            wk = WorkUnit(self.executable_prefix)
            wk.config(x)
            print(wk.command)
            self.workload.add_unit(wk)


    def test_app(self, device, app):
        self.__load_app_workload(device, app.package_name)
        for i, wk_unit in enumerate(self.workload.work_units):
            device.unlock_screen()
            time.sleep(1)
            self.profiler.init()
            self.profiler.start_profiling()
            #app.start()
            time.sleep(3)
            print(wk_unit)
            log_file = os.path.join(app.curr_local_dir, f"test_{i}.logcat")
            self.execute_test(app.package_name, wk_unit, **{'log_filename': log_file})
            #app.stop()
            self.profiler.stop_profiling()
            self.profiler.export_results(f"GreendroidResultTrace{i}.csv")
            print(app.curr_local_dir)
            self.profiler.pull_results(f"GreendroidResultTrace{i}.csv", app.curr_local_dir)
            app.clean_cache()
            break