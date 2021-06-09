import os
from os import listdir


from src.Config import SUPPORTED_PROFILERS, SUPPORTED_TESTING_FRAMEWORKS, SUPPORTED_ANALYZERS, SUPPORTED_INSTRUMENTERS, \
    SUPPORTED_INSTRUMENTATION_TYPES, SUPPORTED_SUITES, SUPPORTED_BUILDING_SYSTEMS
from src.Types import PROFILER, INSTRUMENTER, TESTING_FRAMEWORK, ANALYZER, BUILD_SYSTEM
from src.application.AndroidProject import AndroidProject, BUILD_TYPE
from src.application.Application import App
from src.build.GradleBuilder import GradleBuilder
from src.device.Device import get_first_connected_device

from src.instrument.JInstInstrumenter import JInstInstrumenter
from src.instrument.Types import INSTRUMENTATION_TYPE
from src.profiler.ManafaProfiler import ManafaProfiler
from src.profiler.TrepnProfiler import TrepnProfiler
from src.results_analysis.AnaDroidAnalyzer import AnaDroidAnalyzer
from src.testing_framework.AppCrawlerFramework import AppCrawlerFramework
from src.testing_framework.DroidBotFramework import DroidBotFramework
from src.testing_framework.JUnitBasedFramework import JUnitBasedFramework
from src.testing_framework.MonkeyFramework import MonkeyFramework
from src.testing_framework.MonkeyRunnerFramework import MonkeyRunnerFramework
from src.testing_framework.RERANFramework import RERANFramework
from src.utils.Utils import mega_find


def init_defaultPyAnaDroid(apps_dir):
    return PyAnaDroid(apps_dir=apps_dir,
                      testing_framework=TESTING_FRAMEWORK.DROIDBOT,
                      profiler=PROFILER.MANAFA,
                      build_type=BUILD_TYPE.DEBUG,
                      instrumentation_type=INSTRUMENTATION_TYPE.ANNOTATION
    )


class PyAnaDroid(object):
    def __init__(self, apps_dir, results_dir="results", profiler=PROFILER.MANAFA,
                 testing_framework=TESTING_FRAMEWORK.MONKEY, device=None, instrumenter=INSTRUMENTER.JINST,
                 analyzer=ANALYZER.ANADROID_ANALYZER, instrumentation_type=INSTRUMENTATION_TYPE.TEST, build_system=BUILD_SYSTEM.GRADLE, build_type=BUILD_TYPE.DEBUG):
        self.apps_dir = apps_dir
        self.device = device if device is not None else get_first_connected_device()
        self.results_dir = results_dir
        self.profiler = self.__infer_profiler(profiler)
        self.testing_framework = self.__infer_testing_framework(testing_framework)
        self.instrumentation_type = self.__infer_instrumentation_type(instrumentation_type)
        self.__validate_suite(profiler)
        self.instrumenter = self.__infer_instrumenter(instrumenter)
        self.analyzer = self.__infer_analyzer(analyzer)
        self.builder = self.__infer_build_system(build_system)
        self.resources_dir = "resources"
        self.build_type = build_type

    def __infer_profiler(self, profiler):
        if profiler in SUPPORTED_PROFILERS:
            if profiler == PROFILER.TREPN:
                return TrepnProfiler(profiler.name, self.device)
            elif profiler == PROFILER.MANAFA:
                return ManafaProfiler(profiler.name, self.device)
            elif profiler == PROFILER.GREENSCALER:
                #return GreenScalerProfiler(profiler.name, self.device)
                return None
        else:
            raise Exception("Unsupported profiler")

    def __infer_testing_framework(self, tf):
        if tf in SUPPORTED_TESTING_FRAMEWORKS:
            if tf == TESTING_FRAMEWORK.MONKEY:
                return MonkeyFramework(default_workload=True, profiler=self.profiler)
            elif tf == TESTING_FRAMEWORK.RERAN:
                return RERANFramework(self.device, profiler=self.profiler)
            elif tf == TESTING_FRAMEWORK.APP_CRAWLER:
                return AppCrawlerFramework(default_workload=True,profiler=self.profiler)
            elif tf == TESTING_FRAMEWORK.MONKEY_RUNNER:
                return MonkeyRunnerFramework(default_workload=True,profiler=self.profiler)
            elif tf == TESTING_FRAMEWORK.JUNIT:
                return JUnitBasedFramework(profiler=self.profiler)
            elif tf == TESTING_FRAMEWORK.DROIDBOT:
                return DroidBotFramework(profiler=self.profiler)
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


    def __infer_build_system(self, build_system):
        if build_system in SUPPORTED_BUILDING_SYSTEMS:
            return build_system
        else:
            raise Exception("Unsupported Analyzer")


    def __infer_instrumentation_type(self, test_orientation):
        if test_orientation in SUPPORTED_INSTRUMENTATION_TYPES:
            if test_orientation == INSTRUMENTATION_TYPE.TEST:
                return test_orientation
            elif test_orientation == INSTRUMENTATION_TYPE.ANNOTATION:
                return test_orientation
            elif test_orientation == INSTRUMENTATION_TYPE.METHOD:
                return test_orientation
        else:
            raise Exception("Unsupported instrumentation")

    def init_builder(self, instr_proj):
        if self.builder == BUILD_SYSTEM.GRADLE:
            return GradleBuilder(instr_proj, self.device, self.resources_dir, self.instrumenter)
        return None

    def defaultWorkflow(self):
        app_projects = self.load_projects()
        for app_proj in app_projects:
            app_name = os.path.basename(app_proj)
            print("Processing app " + app_name)
            original_proj = AndroidProject(projname=app_name, projdir=app_proj)
            instrumented_proj_dir = self.instrumenter.instrument(original_proj, instr_type=self.instrumentation_type)
            instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir, results_dir=self.results_dir)
            builder = self.init_builder(instr_proj)
            builder.build_proj_and_apk(build_type=self.build_type, build_tests_apk=self.testing_framework.id==TESTING_FRAMEWORK.JUNIT )
            installed_apps_list = builder.install_apks(build_type=self.build_type, install_apk_test=self.testing_framework.id==TESTING_FRAMEWORK.JUNIT)
            self.do_work(instr_proj, installed_apps_list)
            builder.uninstall_all_apks()

    def do_work(self, proj, apps):
        for i, app in enumerate(apps):
            print("testing package " + app.package_name)
            #app = App(self.device, proj, pkg, local_res=proj.results_dir)
            app.init_local_test_(self.testing_framework.id, self.instrumentation_type)
            app.set_immersive_mode()
            self.testing_framework.init_default_workload(pkg=app.package_name)
            self.testing_framework.test_app(self.device, app)
            self.device.uninstall_pkg(app.package_name)
            #self.analyzer.analyze(app, proj, self.instrumentation_type, self.testing_framework)

    def __validate_suite(self, profiler):
        if not self.instrumentation_type in SUPPORTED_SUITES[profiler]:
            raise Exception(f"{self.instrumentation_type.value} based-instrumentation not supported with {profiler.value}")

    def just_build_apps(self):
        app_projects = self.load_projects()
        for app_proj in app_projects:
            app_name = os.path.basename(app_proj)
            print("Processing app " + app_name + " in " + app_proj)
            original_proj = AndroidProject(projname=app_name, projdir=app_proj)
            instrumented_proj_dir = self.instrumenter.instrument(original_proj, instr_type=self.instrumentation_type)
            instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir, results_dir=self.results_dir)
            builder = self.init_builder(instr_proj)
            builder.build_proj_and_apk(build_type=self.build_type,
                                       build_tests_apk=self.testing_framework.id == TESTING_FRAMEWORK.JUNIT)
            app_list = builder.install_apks(build_type=self.build_type,
                                 install_apk_test=self.testing_framework.id == TESTING_FRAMEWORK.JUNIT)
            builder.uninstall_all_apks()

    def load_projects(self):
        return_projs = []
        if is_android_project(self.apps_dir):
            potential_projects = [self.apps_dir]
        else:
            potential_projects = list(filter(lambda x: os.path.isdir(os.path.join(self.apps_dir, x)), os.listdir(self.apps_dir)))
        for maybe_proj in potential_projects:
            path_dir = os.path.join(self.apps_dir, maybe_proj)
            has_gradle_right_next = mega_find(path_dir, pattern="build.gradle", maxdepth=1, type_file='f')
            if len(has_gradle_right_next) > 0:
                return_projs.append(path_dir)
            else:
                children_dirs = list(filter(lambda x: os.path.isdir(os.path.join(path_dir, x)), os.listdir(path_dir)))
                for child in children_dirs:
                    child_path_dir = os.path.join(path_dir, child)
                    has_gradle_right_next = mega_find(child_path_dir, pattern="build.gradle", maxdepth=1, type_file='f')
                    if len(has_gradle_right_next) > 0:
                        return_projs.append(child_path_dir)
        return return_projs

def is_android_project(dirpath):
    return "settings.gradle" in [f for f in listdir(dirpath)]


if __name__ == '__main__':
    #folder_of_apps = "/Users/ruirua/repos/pyAnaDroid/old_apps/outDir/PDFConverter"
    folder_of_apps = "/Users/ruirua/repos/pyAnaDroid/demoProjects/SampleApp"
    anadroid = init_defaultPyAnaDroid(folder_of_apps)
    anadroid.defaultWorkflow()
    #anadroid.just_build_apps()
