import argparse
import os
import re
import traceback
from anadroid.Config import SUPPORTED_PROFILERS, SUPPORTED_TESTING_FRAMEWORKS, SUPPORTED_ANALYZERS, \
    SUPPORTED_INSTRUMENTERS, \
    SUPPORTED_INSTRUMENTATION_TYPES, SUPPORTED_SUITES, SUPPORTED_BUILDING_SYSTEMS
from anadroid.Types import PROFILER, INSTRUMENTER, TESTING_FRAMEWORK, ANALYZER, BUILD_SYSTEM
from anadroid.application.AndroidProject import AndroidProject, BUILD_TYPE, is_android_project, Project
from anadroid.application.Application import App
from anadroid.build.GradleBuilder import GradleBuilder
from anadroid.device.Device import get_first_connected_device
from anadroid.instrument.JInstInstrumenter import JInstInstrumenter
from anadroid.instrument.NoneInstrumenter import NoneInstrumenter
from anadroid.instrument.Types import INSTRUMENTATION_TYPE
from anadroid.profiler.GreenScalerProfiler import GreenScalerProfiler
from anadroid.profiler.ManafaProfiler import ManafaProfiler
from anadroid.profiler.NoneProfiler import NoneProfiler
from anadroid.profiler.TrepnProfiler import TrepnProfiler
from anadroid.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
from anadroid.results_analysis.ComposedAnalyzer import ComposedAnalyzer
from anadroid.results_analysis.LogAnalyzer import LogAnalyzer
from anadroid.results_analysis.ManafaAnalyzer import ManafaAnalyzer
from anadroid.results_analysis.ManafaMethodCoverageAnalyzer import ManafaMethodCoverageAnalyzer
from anadroid.results_analysis.OldAnaDroidAnalyzer import OldAnaDroidAnalyzer
from anadroid.results_analysis.SCCAnalyzer import SCCAnalyzer
from anadroid.testing_framework.AppCrawlerFramework import AppCrawlerFramework
from anadroid.testing_framework.CustomCommandFramework import CustomCommandFramework
from anadroid.testing_framework.DroidBotFramework import DroidBotFramework
from anadroid.testing_framework.JUnitBasedFramework import JUnitBasedFramework
from anadroid.testing_framework.MonkeyFramework import MonkeyFramework
from anadroid.testing_framework.MonkeyRunnerFramework import MonkeyRunnerFramework
from anadroid.testing_framework.RERANFramework import RERANFramework
from anadroid.utils.Utils import mega_find, extract_pkg_name_from_apk, get_results_dir, logw, logi, loge, \
    get_resources_dir, get_log_dir



class AnaDroid(object):
    """Provides a configurable pipeline to benchmark and analyze Android Projects and Applications.
    This class provides a set of verifications and workflow that allows to automatically perform tasks involved in
    mobile software analysis. Any class can extend this class to customize its workflow and perform customized benchmarks.
    Attributes:
        device(Device): device to be used.
        app_projects_ut(list): Android Projects to process.
        tests_dir(str): directory containing app tests (only used with RERAN).
        rebuild_apps(bool): optionally rebuild apps from Android Projects already built.
        reinstrument(bool): optionally reinstrument Android Projects previously instrumented.
        apps(list): list of apps to exercise.
        apks(list): list of apks to exercise.
        results_dir(str): directory where results will be stored.
        instrumentation_type(INSTRUMENTATION_TYPE): instrumentation type.
        profiler(AbstractProfiler): profiler to be used.
        analyzer(AbstractAnalyzer): analyzer to parse and generate results from framework executions.
        testing_framework(AbstractTestingFramework): testing framework to be used.
        instrumenter(AbstractInstrumenter): instrumentation tool to be used.
        builder(AbstractBuilder): building system to build apps.
        resources_dir(str): directory with framework resources.
        build_type(BUILD_TYPE): type of build to produce in the Android Projects.
    """
    def __init__(self, arg1, results_dir=get_results_dir(), profiler=PROFILER.MANAFA,
                 testing_framework=TESTING_FRAMEWORK.MONKEY, device=None, instrumenter=INSTRUMENTER.JINST,
                 analyzer=ANALYZER.OLD_ANADROID_ANALYZER, instrumentation_type=INSTRUMENTATION_TYPE.ANNOTATION,
                 build_system=BUILD_SYSTEM.GRADLE, build_type=BUILD_TYPE.DEBUG, tests_dir=None, rebuild_apps=False,
                 reinstrument=False, recover_from_last_run=False, test_cmd=None, load_projects=True):
        self.device = device if device is not None else get_first_connected_device()
        self.app_projects_ut = []
        self.tests_dir = tests_dir
        self.rebuild_apps = rebuild_apps
        self.reinstrument = reinstrument
        self.apps = [] # apps created from package names passed by argument
        self.apks = [] # apk paths passed by argument
        self.recover_from_last_run = recover_from_last_run
        if isinstance(arg1, argparse.Namespace):
            self.__setup_from_argparse(arg1)
        else:
            self.apps_dir = os.path.realpath(arg1)
            self.app_projects_ut = self.load_projects() if load_projects else []
        self.results_dir = results_dir
        self.test_cmd = test_cmd
        self.instrumentation_type = self.__infer_instrumentation_type(instrumentation_type)
        self.profiler = self.__infer_profiler(profiler)
        self.analyzer = self.__infer_analyzer(analyzer, profiler)
        self.testing_framework = self.__infer_testing_framework(testing_framework)
        self.__validate_suite(profiler)
        self.instrumenter = self.__infer_instrumenter(instrumenter)
        self.builder = self.__infer_build_system(build_system)
        self.resources_dir = get_resources_dir()
        self.build_type = build_type

    def __setup_from_argparse(self, args: argparse.Namespace):
        """get configs from argparse object if provided in app constructor.
        Args:
            args: argparse object containing user preferences.
        """
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
        """creates App objects from a list of package names.
        Args:
            package_names(list): list of package names.
        """
        self.apps = []
        for pkg in package_names:
            da_proj = Project(pkg, pkg)
            da_proj.init_results_dir(pkg)
            self.apps.append(App(self.device, da_proj, pkg, apk_path=None, local_res_dir=da_proj.results_dir))

    @staticmethod
    def __create_apps_from_apk_names(apk_list):
        return apk_list
        '''for apk in apk_list:
            if not os.path.exists(apk):
                #raise FileNotFoundError()
            pkg = extract_pkg_name_from_apk(apk)
            da_proj = Project(pkg, pkg)
            da_proj.init_results_dir(pkg)
            self.apks.append( App(self.device, da_proj, pkg,apk_path=apk, local_res=da_proj.results_dir) )'''

    def __infer_profiler(self, profiler):
        """infers profiler from profiler enum.
        Args:
            profiler(PROFILER): profiler enum selected by user.
        Returns:
            concrete_profiler(AbstractProfiler): inferred profiler.
        """
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
        """infers testing framework from TESTING_FRAMEWORK enum.
        Args:
            tf(TESTING_FRAMEWORK): TESTING_FRAMEWORK enum selected by user.
        Returns:
            concrete_testing_framework(AbstractTestingFramework): inferred framework.
        """
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
            elif tf == TESTING_FRAMEWORK.CUSTOM:
                if self.test_cmd is None:
                    raise Exception("Unable to execute CustomCommandFramework without providing a command as input")
                return CustomCommandFramework(default_workload=True, profiler=self.profiler, analyzer=self.analyzer,
                                              command=self.test_cmd)
            else:
                return None
        else:
            raise Exception("Unsupported Testing framework")

    def __infer_instrumenter(self, inst):
        """infers instrumentation tool from INSTRUMENTER enum.
        Args:
            inst(INSTRUMENTER): INSTRUMENTER enum selected by user.
        Returns:
            concrete_instrumenter(AbstractTestingFramework): inferred instrumenter.
        """
        if inst in SUPPORTED_INSTRUMENTERS:
            if inst == INSTRUMENTER.JINST:
                return JInstInstrumenter(self.profiler)
            elif inst == INSTRUMENTER.NONE:
                return NoneInstrumenter(self.profiler)
            else:
                return None
        else:
            raise Exception("Unsupported instrumenter")

    def __infer_analyzer(self, ana, profiler):
        """infers analyzer tool from ANALYZER and PROFILER enums.
        Args:
            ana(ANALYZER): ANALYZER enum selected by user.
            profiler(PROFILER): PROFILER enum selected by user.
        Returns:
            AbstractAnalyzer: inferred analyzer.
        """
        analyzers = [LogAnalyzer(self.profiler), ApkAPIAnalyzer(self.profiler)]
        if len(self.apps) > 0:
            analyzers.append(SCCAnalyzer(self.profiler))
        if not ana in SUPPORTED_ANALYZERS:
            raise Exception(f"Unsupported Analyzer {ana}")
        if profiler == profiler.TREPN:
            analyzers.append(OldAnaDroidAnalyzer(self.profiler))
        elif profiler == profiler.MANAFA and ana == ANALYZER.MANAFA_ANALYZER:
            analyzers.append(ManafaAnalyzer(self.profiler))
            analyzers.append(ManafaMethodCoverageAnalyzer(self.profiler))
        return ComposedAnalyzer(self.profiler, analyzers)

    def __infer_build_system(self, build_system):
        if build_system in SUPPORTED_BUILDING_SYSTEMS:
            return build_system
        else:
            raise Exception("Unsupported Analyzer")

    def __infer_instrumentation_type(self, test_orientation):
        """validates instrumentation type.
        Returns:
            INSTRUMENTATION_TYPE: instrumentation type.
        """
        if test_orientation in SUPPORTED_INSTRUMENTATION_TYPES:
            return test_orientation
        else:
            raise Exception("Unsupported instrumentation")

    def init_builder(self, instr_proj):
        if self.builder == BUILD_SYSTEM.GRADLE:
            return GradleBuilder(instr_proj, self.device, self.resources_dir, self.instrumenter)
        return None

    def default_workflow(self):
        """performs the basic workflow involved in processing apps straight from the source code.
        For each app, project or apk provided to pynadroid, performs the required steps to transform such inputs
        in software ready to be used and tested on the connected device, using the selected testing framework.
        """
        for app_proj in self.app_projects_ut:
            instr_proj, builder = self.build_app_project(app_proj, build_apks=True)
            if builder is None:
                continue
            installed_apps_list = self.device.install_apks(instr_proj, build_type=self.build_type,
                                                           install_test_apks=self.needs_tests_apk())
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
            self.do_work([App(self.device, da_proj, pkg, apk_path=apk, local_res_dir=da_proj.results_dir)])
            self.device.uninstall_pkg(pkg)

        self.do_work(self.apps)

    def do_work(self, apps):
        """Executes the testing framework for each app in apps."""
        for i, app in enumerate(apps):
            logi("testing app package " + app.package_name)
            try:
                app.init_local_test_(self.testing_framework.id, self.instrumentation_type)
                self.device.unlock_screen()
                app.set_immersive_mode()
                self.testing_framework.init_default_workload(pkg=app.package_name, tests_dir=self.tests_dir)
                self.testing_framework.test_app(self.device, app)
                self.device.uninstall_pkg(app.package_name)

                self.analyzer.analyze_tests(app, **{'instr_type': self.instrumentation_type,
                                                    'testing_framework': self.testing_framework,
                                                    })
            except Exception:
                loge(traceback.format_exc())

    def exec_command(self):
        try:
            self.testing_framework.init_default_workload()
            self.testing_framework.test_app(self.device, app=None)
            self.analyzer.analyze_tests(results_dir=self.testing_framework.get_default_test_dir(), **{
                                                'testing_framework': self.testing_framework,
                                                })
        except Exception:
            loge(traceback.format_exc())


    def __validate_suite(self, profiler):
        """checks if the selected profiler can be combined with the selected instrumentation tyoe.
        Args:
            profiler(PROFILER): profiler.
        """
        if not self.instrumentation_type in SUPPORTED_SUITES[profiler]:
            raise Exception(
                f"{self.instrumentation_type.value} based-instrumentation not supported with {profiler.value}")

    def just_build_apps(self):
        """builds apps from app_projects_ut."""
        for app_proj in self.app_projects_ut:
            self.build_app_project(app_proj, build_apks=True)

    def build_app_project(self, app_project, build_apks=False):
        app_name = os.path.basename(app_project)
        logi("Processing app " + app_name + " in " + app_project)
        res = False
        instr_proj = None
        builder = None
        try:
            original_proj = AndroidProject(projname=app_name, projdir=app_project, clean_instrumentations=self.reinstrument)
            instrumented_proj_dir = self.instrumenter.instrument(original_proj, instr_type=self.instrumentation_type)
            instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir, results_dir=self.results_dir)
            builder = self.init_builder(instr_proj)
            if build_apks:
               res = builder.build_proj_and_apk(build_type=self.build_type, build_tests_apk=self.testing_framework.id == TESTING_FRAMEWORK.JUNIT)
            else:
                res = builder.build()
        except Exception:
            loge(traceback.format_exc())

        if not res:
            loge(f"Unable to build {app_name}. Skipping app")
            return instr_proj, None
        return instr_proj, builder

    def just_analyze(self):
        """analyze apps obtained from app_projects_ut."""
        for app_proj in self.app_projects_ut:
            app_name = os.path.basename(app_proj)
            logi("Processing app " + app_name + " in " + app_proj)
            original_proj = AndroidProject(projname=app_name, projdir=app_proj)
            app = App(self.device, original_proj, original_proj.pkg_name, apk_path="",
                      local_res_dir=original_proj.results_dir)
            raise NotImplementedError()
            # builder = self.init_builder(instr_proj)
            # builder.build_proj_and_apk(build_type=self.build_type,build_tests_apk=self.testing_framework.id == TESTING_FRAMEWORK.JUNIT)
            # self.analyzer.analyze(app, **{'instr_type': self.instrumentation_type, 'testing_framework': self.testing_framework})

    def __get_project_root_dir(self, dir_path):
        """infers Android project root directory."""
        has_gradle_right_next = mega_find(dir_path, pattern="build.gradle", maxdepth=4, type_file='f')
        if len(has_gradle_right_next) > 0:
            top_gradle_file = min(has_gradle_right_next, key=len)
            return os.path.dirname(top_gradle_file) if top_gradle_file is not None else None
        return None

    def load_projects(self):
        """loads Android Projects from a directory containing one or more projects."""
        return_projs = []
        if is_android_project(self.apps_dir):
            potential_projects = [self.apps_dir]
        else:
            potential_projects = list(
                filter(lambda x: os.path.isdir(os.path.join(self.apps_dir, x)), os.listdir(self.apps_dir)))
        for maybe_proj in potential_projects:
            path_dir = os.path.join(self.apps_dir, maybe_proj)
            proj_fldr = self.__get_project_root_dir(path_dir)
            if proj_fldr is not None:
                return_projs.append(proj_fldr)
            else:
                children_dirs = list(filter(lambda x: os.path.isdir(os.path.join(path_dir, x)), os.listdir(path_dir)))
                for child in children_dirs:
                    child_path_dir = os.path.join(path_dir, child)
                    proj_fldr = self.__get_project_root_dir(child_path_dir)
                    if proj_fldr is not None:
                        return_projs.append(proj_fldr)

        if self.recover_from_last_run:
            projs_to_exclude = self.get_projs_from_last_run()
            return_projs = [x for x in return_projs if x not in projs_to_exclude]
            if len(return_projs) == 0:
                logw(f"All projects executed in the last run or no projects found in {self.apps_dir}")
        return return_projs

    def get_projs_from_last_run(self):
        processed_projs_last_run = []
        file_lines = []
        regex = r"Processing app "
        last_run_file = self.get_last_run_file()
        if last_run_file is None:
            return []
        with open(last_run_file, 'r') as file:
            file_lines = file.readlines()
        for line in file_lines:
            if re.search(regex, line):
                proj_dir = line.split("in ")[1].strip()
                processed_projs_last_run.append(proj_dir)
        return processed_projs_last_run

    def get_last_run_file(self):
        run_regex = r"\d+-\d+-\d+-\d+-\d+.*.log"
        log_dir = get_log_dir()
        if not os.path.exists(log_dir):
            return None
        prev_logs = list(filter(lambda t: re.search(run_regex, t), mega_find(log_dir, pattern='*.log', type_file='f', maxdepth=1)))
        if len(prev_logs) == 0:
            return None
        sorted_list = sorted(prev_logs, key=os.path.getmtime)
        return sorted_list[-1]

    def record_test(self, tests_dir=None):
        """records tests that can be replayed later.
        Args:
            tests_dir: directory to store tests.
        """
        if self.testing_framework.is_recordable():
            self.testing_framework.record_test(output_dir=tests_dir)
        else:
            raise Exception(f"Unable to record test with {self.testing_framework.id.value} framework")

    def needs_tests_apk(self):
        """checks if the selected testing framework requires a tests apk.
        Returns:
            bool: True if os a JUnit-based testing framework, False otherwise.
        """
        return self.testing_framework.id in [TESTING_FRAMEWORK.JUNIT,
                                             TESTING_FRAMEWORK.ESPRESSO, TESTING_FRAMEWORK.ROBOTIUM]

