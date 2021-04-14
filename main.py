import os, time


from src.Types import PROFILER, INSTRUMENTER, TESTING_FRAMEWORK, ANALYZER, SUPPORTED_PROFILERS, \
    SUPPORTED_TESTING_FRAMEWORKS, SUPPORTED_INSTRUMENTERS, SUPPORTED_INSTRUMENTATION_TYPES, SUPPORTED_ANALYZERS
from src.application.AndroidProject import AndroidProject, BUILD_TYPE
from src.application.Application import App
from src.build.GradleBuilder import GradleBuilder

from src.device.Device import Device, get_first_connected_device
from src.instrument.JInstInstrumenter import JInstInstrumenter
from src.instrument.Types import INSTRUMENTATION_TYPE
from src.profiler.TrepnProfiler import TrepnProfiler
from src.results_analysis.AnaDroidAnalyzer import AnaDroidAnalyzer
from src.testing_framework.MonkeyFramework import MonkeyFramework


MIN_API_LEVEL = 9
MAX_API_LEVEL = 30


def init_defaultPyAnaDroid(apps_dir):
    return PyAnaDroid(apps_dir=apps_dir)

class PyAnaDroid(object):
    def __init__(self, apps_dir, results_dir="results", profiler=PROFILER.TREPN, testing_framework=TESTING_FRAMEWORK.MONKEY, device=get_first_connected_device(), instrumenter=INSTRUMENTER.JINST, analyzer=ANALYZER.ANADROID_ANALYZER,instrumentation_type=INSTRUMENTATION_TYPE.ANNOTATION ):
        self.apps_dir = apps_dir
        self.device = device
        self.results_dir = results_dir
        self.profiler = self.__infer_profiler(profiler)
        self.testing_framework = self.__infer_testing_framework(testing_framework)
        self.instrumentation_type = self.__infer_instrumentation_type(instrumentation_type)
        self.instrumenter = self.__infer_instrumenter(instrumenter)
        self.analyzer = self.__infer_analyzer(analyzer)
        self.resources_dir = "resources"


    def __infer_profiler(self, profiler):
        if profiler in SUPPORTED_PROFILERS:
            if profiler == PROFILER.TREPN:
                return TrepnProfiler(self.device)
        else:
            raise Exception("Unsupported profiler")

    def __infer_testing_framework(self, tf):
        if tf in SUPPORTED_TESTING_FRAMEWORKS:
            if tf == TESTING_FRAMEWORK.MONKEY:
                return MonkeyFramework(default_workload=True)
            else:
                return None
        else:
            raise Exception("Unsupported Testing framework")

    def __infer_instrumenter(self, inst):
        if inst in SUPPORTED_INSTRUMENTERS:
            if inst == INSTRUMENTER.JINST:
                return JInstInstrumenter(self.profiler)
            else:
                return None
        else:
            raise Exception("Unsupported instrumenter")

    def __infer_analyzer(self, ana):
        if ana in SUPPORTED_ANALYZERS:
            if ana == ANALYZER.ANADROID_ANALYZER:
                return AnaDroidAnalyzer()
            else:
                return None
        else:
            raise Exception("Unsupported Analyzer")

    def __infer_instrumentation_type(self, test_orientation):
        if test_orientation in SUPPORTED_INSTRUMENTATION_TYPES:
            if test_orientation == INSTRUMENTATION_TYPE.TEST:
                return test_orientation
            elif test_orientation == INSTRUMENTATION_TYPE.ANNOTATION:
                return test_orientation
        else:
            raise Exception("Unsupported instrumentation")

    def defaultWorkflow(self):
        app_projects = list(filter(lambda x: os.path.isdir(os.path.join(self.apps_dir, x)), os.listdir(self.apps_dir)))
        for app_name in app_projects:
            print("Processing app " + app_name)
            original_proj = AndroidProject(projname=app_name, projdir=self.apps_dir + "/" + app_name)
            instrumented_proj_dir = self.instrumenter.instrument(original_proj,instr_type=self.instrumentation_type)
            instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir, results_dir=self.results_dir)
            builder = GradleBuilder(instr_proj, self.device, self.resources_dir, self.instrumenter)
            builder.build_proj_and_apk(build_type=BUILD_TYPE.RELEASE)
            installed_pkgs = self.device.install_apks(instr_proj)
            self.do_work(instr_proj, installed_pkgs)


    def do_work(self, proj, pkgs):
        for i, pkg in enumerate(pkgs):
            print("testing package " + pkg)
            app = App(self.device, proj, pkg, local_res=proj.results_dir)
            app.init_local_test_(self.testing_framework.id, self.instrumentation_type)
            app.set_immersive_mode()
            for wk_unit in self.testing_framework.workload.work_units:
                self.device.unlock_screen()
                time.sleep(1)
                self.profiler.init()
                self.profiler.start_profiling()
                app.start()
                time.sleep(1)
                self.testing_framework.execute_test(pkg, wk_unit)
                app.stop()
                self.profiler.stop_profiling()
                self.profiler.export_results("GreendroidResultTrace0.csv")
                self.profiler.pull_results("GreendroidResultTrace0.csv", app.curr_local_dir)
                app.clean_cache()
                break
            self.device.uninstall_pkg(pkg)
            self.analyzer.analyze(app, proj, self.instrumentation_type, self.testing_framework)

if __name__ == '__main__':
    folder_of_apps = "/Users/ruirua/repos/pyAnaDroid/demoProjects/"
    anadroid = init_defaultPyAnaDroid(folder_of_apps)
    anadroid.defaultWorkflow()