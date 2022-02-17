import argparse
import os
from os import listdir


from anadroid.Config import SUPPORTED_PROFILERS, SUPPORTED_TESTING_FRAMEWORKS, SUPPORTED_ANALYZERS, \
    SUPPORTED_INSTRUMENTERS, \
    SUPPORTED_INSTRUMENTATION_TYPES, SUPPORTED_SUITES, SUPPORTED_BUILDING_SYSTEMS
from anadroid.Types import PROFILER, INSTRUMENTER, TESTING_FRAMEWORK, ANALYZER, BUILD_SYSTEM
from anadroid.application.AndroidProject import AndroidProject, BUILD_TYPE, is_android_project, Project
from anadroid.application.Application import App
from anadroid.build.GradleBuilder import GradleBuilder
from anadroid.device.Device import get_first_connected_device

from anadroid.instrument.JInstInstrumenter import JInstInstrumenter
from anadroid.instrument.Types import INSTRUMENTATION_TYPE
from anadroid.profiler.GreenScalerProfiler import GreenScalerProfiler
from anadroid.profiler.ManafaProfiler import ManafaProfiler
from anadroid.profiler.NoneProfiler import NoneProfiler
from anadroid.profiler.TrepnProfiler import TrepnProfiler
from anadroid.results_analysis.ComposedAnalyzer import ComposedAnalyzer
from anadroid.results_analysis.LogAnalyzer import LogAnalyzer
from anadroid.results_analysis.ManafaAnalyzer import ManafaAnalyzer
from anadroid.results_analysis.OldAnaDroidAnalyzer import OldAnaDroidAnalyzer
from anadroid.results_analysis.SCCAnalyzer import SCCAnalyzer
from anadroid.testing_framework.AppCrawlerFramework import AppCrawlerFramework
from anadroid.testing_framework.DroidBotFramework import DroidBotFramework
from anadroid.testing_framework.JUnitBasedFramework import JUnitBasedFramework
from anadroid.testing_framework.MonkeyFramework import MonkeyFramework
from anadroid.testing_framework.MonkeyRunnerFramework import MonkeyRunnerFramework
from anadroid.testing_framework.RERANFramework import RERANFramework
from anadroid.utils.Utils import mega_find, extract_pkg_name_from_apk, get_results_dir, logw, logi, loge


class AnaDroid(object):
    def __init__(self, arg1, results_dir=get_results_dir(), profiler=PROFILER.MANAFA,
                 testing_framework=TESTING_FRAMEWORK.MONKEY, device=None, instrumenter=INSTRUMENTER.JINST,
                 analyzer=ANALYZER.OLD_ANADROID_ANALYZER, instrumentation_type=INSTRUMENTATION_TYPE.ANNOTATION,
                 build_system=BUILD_SYSTEM.GRADLE, build_type=BUILD_TYPE.DEBUG, tests_dir=None, rebuild_apps=False, reinstrument=False):
        self.device = device if device is not None else get_first_connected_device()
        self.app_projects_ut = []
        self.tests_dir = tests_dir
        self.rebuild_apps = rebuild_apps
        self.reinstrument = reinstrument
        self.apps = [] # apps created from package names passed by argument
        self.apks = [] # apk paths passed by argument
        if isinstance(arg1, argparse.Namespace):
            self.__setup_from_argparse(arg1)
        else:
            self.apps_dir = os.path.realpath(arg1)
            self.app_projects_ut = self.load_projects()
        self.results_dir = results_dir
        self.instrumentation_type = self.__infer_instrumentation_type(instrumentation_type)
        self.profiler = self.__infer_profiler(profiler)
        self.analyzer = self.__infer_analyzer(analyzer, profiler)
        self.testing_framework = self.__infer_testing_framework(testing_framework)
        self.__validate_suite(profiler)
        self.instrumenter = self.__infer_instrumenter(instrumenter)
        self.builder = self.__infer_build_system(build_system)
        self.resources_dir = "resources"
        self.build_type = build_type

    def __setup_from_argparse(self, args: argparse.Namespace):
        if len(args.application_packages) > 0:
            if args.buildonly:
                raise Exception("incompatible option -bi. APKs are already built")
            self.apps_dir = []
            self.apks = self.__create_apps_from_apk_names(args.application_packages)
        elif len(args.package_names) > 0:
            if args.buildonly:
                raise Exception("incompatible option -bi. trying to process already built and installed apps")
            self.apps_dir = []
            self.__create_apps_from_package_names(args.package_names)
        logw("ignoring instrumentation phase")

    def __create_apps_from_package_names(self, package_names):
        self.apps = []
        for pkg in package_names:
            da_proj = Project(pkg, pkg)
            da_proj.init_results_dir(pkg)
            self.apps.append(App(self.device, da_proj, pkg, apk_path="", local_res=da_proj.results_dir))

    def __create_apps_from_apk_names(self, apk_list):
        return apk_list
        '''for apk in apk_list:
            if not os.path.exists(apk):
                print("olha que nao ha")
                #raise FileNotFoundError()
            pkg = extract_pkg_name_from_apk(apk)
            da_proj = Project(pkg, pkg)
            da_proj.init_results_dir(pkg)
            self.apks.append( App(self.device, da_proj, pkg,apk_path=apk, local_res=da_proj.results_dir) )'''

    def __infer_profiler(self, profiler):
        if profiler in SUPPORTED_PROFILERS:
            if profiler == PROFILER.TREPN:
                return TrepnProfiler(profiler, self.device)
            elif profiler == PROFILER.MANAFA:
                return ManafaProfiler(profiler, self.device,
                                      hunter=self.instrumentation_type == INSTRUMENTATION_TYPE.ANNOTATION)
            elif profiler == PROFILER.GREENSCALER:
                return GreenScalerProfiler(profiler, self.device)
            elif profiler == PROFILER.NONE:
                return NoneProfiler(profiler, self.device)
                # return None
        else:
            raise Exception("Unsupported profiler")

    def __infer_testing_framework(self, tf):
        if tf in SUPPORTED_TESTING_FRAMEWORKS:
            if tf == TESTING_FRAMEWORK.MONKEY:
                return MonkeyFramework(default_workload=True, profiler=self.profiler, analyzer=self.analyzer)
            elif tf == TESTING_FRAMEWORK.RERAN:
                return RERANFramework(self.device, profiler=self.profiler, analyzer=self.analyzer)
            elif tf == TESTING_FRAMEWORK.APP_CRAWLER:
                return AppCrawlerFramework(default_workload=True, profiler=self.profiler, analyzer=self.analyzer)
            elif tf == TESTING_FRAMEWORK.MONKEY_RUNNER:
                return MonkeyRunnerFramework(default_workload=True, profiler=self.profiler, analyzer=self.analyzer)
            elif tf == TESTING_FRAMEWORK.JUNIT:
                return JUnitBasedFramework(profiler=self.profiler, analyzer=self.analyzer)
            elif tf == TESTING_FRAMEWORK.DROIDBOT:
                return DroidBotFramework(default_workload=True, profiler=self.profiler, analyzer=self.analyzer)
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

    def __infer_analyzer(self, ana, profiler):
        analyzers = [LogAnalyzer(self.profiler), SCCAnalyzer(self.profiler)]
        if not ana in SUPPORTED_ANALYZERS:
            raise Exception(f"Unsupported Analyzer {ana}")
        if profiler == profiler.TREPN:
            analyzers.append(OldAnaDroidAnalyzer(self.profiler))
        elif profiler == profiler.MANAFA and ana == ANALYZER.MANAFA_ANALYZER:
            analyzers.append(ManafaAnalyzer(self.profiler))

        return ComposedAnalyzer(self.profiler, analyzers)

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

    def default_workflow(self):
        for app_proj in self.app_projects_ut:
            app_name = os.path.basename(app_proj)
            logi("Processing app " + app_name + " in " + app_proj)
            original_proj = AndroidProject(projname=app_name, projdir=app_proj, clean_instrumentations=self.reinstrument)
            instrumented_proj_dir = self.instrumenter.instrument(original_proj, instr_type=self.instrumentation_type)
            instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir, results_dir=self.results_dir)
            builder = self.init_builder(instr_proj)
            res = builder.build_proj_and_apk(build_type=self.build_type, build_tests_apk=self.needs_tests_apk(), rebuild=self.rebuild_apps)
            if not res:
                loge(f"Unable to build {app_name}. Skipping app")
                continue
            installed_apps_list = builder.install_apks(build_type=self.build_type, install_apk_test=self.needs_tests_apk())
            self.do_work(installed_apps_list)
            builder.uninstall_all_apks()
            self.analyzer.show_results(installed_apps_list)

        for apk in self.apks:
            logi(f"installing apk {apk}")
            self.device.install_apk(apk)
            new_pkgs = self.device.get_new_installed_pkgs()
            pkg = new_pkgs[0] if len(new_pkgs) else extract_pkg_name_from_apk(apk)
            logi(f"pkg name {pkg}")
            da_proj = Project(pkg, pkg)
            da_proj.init_results_dir(pkg)
            self.do_work([App(self.device, da_proj, pkg, apk_path=apk, local_res=da_proj.results_dir)])
            self.device.uninstall_pkg(pkg)

        self.do_work(self.apps)

    def do_work(self, apps):
        for i, app in enumerate(apps):
            logi("testing package " + app.package_name)
            app.init_local_test_(self.testing_framework.id, self.instrumentation_type)
            app.set_immersive_mode()
            self.testing_framework.init_default_workload(pkg=app.package_name, tests_dir=self.tests_dir)
            self.testing_framework.test_app(self.device, app)
            self.device.uninstall_pkg(app.package_name)
            self.analyzer.analyze_tests(app, **{'instr_type': self.instrumentation_type,
                                                'testing_framework': self.testing_framework,
                                                })

    def __validate_suite(self, profiler):
        if not self.instrumentation_type in SUPPORTED_SUITES[profiler]:
            raise Exception(
                f"{self.instrumentation_type.value} based-instrumentation not supported with {profiler.value}")

    def just_build_apps(self):
        for app_proj in self.app_projects_ut:
            app_name = os.path.basename(app_proj)
            logi("Processing app " + app_name + " in " + app_proj)
            original_proj = AndroidProject(projname=app_name, projdir=app_proj, clean_instrumentations=self.reinstrument)
            instrumented_proj_dir = self.instrumenter.instrument(original_proj, instr_type=self.instrumentation_type)
            instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir, results_dir=self.results_dir)

            builder = self.init_builder(instr_proj)
            builder.build_proj_and_apk(build_type=self.build_type,
                                       build_tests_apk=self.testing_framework.id == TESTING_FRAMEWORK.JUNIT)

    def just_analyze(self):
        for app_proj in self.app_projects_ut:
            app_name = os.path.basename(app_proj)
            logi("Processing app " + app_name + " in " + app_proj)
            original_proj = AndroidProject(projname=app_name, projdir=app_proj)
            app = App(self.device, original_proj, original_proj.pkg_name, apk_path="",
                      local_res=original_proj.results_dir)
            raise NotImplementedError()
            # builder = self.init_builder(instr_proj)
            # builder.build_proj_and_apk(build_type=self.build_type,build_tests_apk=self.testing_framework.id == TESTING_FRAMEWORK.JUNIT)
            # self.analyzer.analyze(app, **{'instr_type': self.instrumentation_type, 'testing_framework': self.testing_framework})

    def __get_project_from_dir(self, dir_path):
        has_gradle_right_next = mega_find(dir_path, pattern="build.gradle", maxdepth=2, type_file='f')
        if len(has_gradle_right_next) > 0:
            top_gradle_file = min(has_gradle_right_next, key=len)
            return os.path.dirname(top_gradle_file)
        return None

    def load_projects(self):
        return_projs = []
        if is_android_project(self.apps_dir):
            potential_projects = [self.apps_dir]
        else:
            potential_projects = list(
                filter(lambda x: os.path.isdir(os.path.join(self.apps_dir, x)), os.listdir(self.apps_dir)))
        for maybe_proj in potential_projects:
            path_dir = os.path.join(self.apps_dir, maybe_proj)
            proj_fldr = self.__get_project_from_dir(path_dir)
            if proj_fldr is not None:
                return_projs.append(proj_fldr)
            else:
                children_dirs = list(filter(lambda x: os.path.isdir(os.path.join(path_dir, x)), os.listdir(path_dir)))
                for child in children_dirs:
                    child_path_dir = os.path.join(path_dir, child)
                    proj_fldr = self.__get_project_from_dir(child_path_dir)
                    if proj_fldr is not None:
                        return_projs.append(proj_fldr)
        return return_projs

    def record_test(self, tests_dir=None):
        if self.testing_framework.is_recordable():
            self.testing_framework.record_test(output_dir=tests_dir)
        else:
            raise Exception(f"Unable to record test with {self.testing_framework.id.value} framework")

    def needs_tests_apk(self):
        return self.testing_framework.id in [TESTING_FRAMEWORK.JUNIT,
                                             TESTING_FRAMEWORK.ESPRESSO, TESTING_FRAMEWORK.ROBOTIUM]

