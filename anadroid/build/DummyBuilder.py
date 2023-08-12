import os
from shutil import copy

from manafa.utils.Logger import log, LogSeverity
from textops import grep, cat
import json
import re

# Import statements for relevant classes from the project
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.application.Application import App
from anadroid.application.Dependency import DependencyType
from anadroid.build.AbstractBuilder import AbstractBuilder
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import mega_find, execute_shell_command, sign_apk, log_to_file, loge
from anadroid.build.GracleBuildErrorSolver import is_known_error

# Constants
BUILD_RESULTS_FILE = "buildStatus.json"
SUCCESS_VALUE = "Success"
ERROR_VALUE = "Error"
BUILD_SUCCESS_VALUE = "BUILD SUCCESSFUL"
DEFAULT_BUILD_TIMES_TO_TRY = 5
DEFAULT_BUILD_TOOLS_VERSION = '25.0.3'  # TODO: Decide on the default build tools version

# Global variable for transitive dependency keyword
TRANSITIVE = None


def gen_dependency_string(dependency):
    """Generates the dependency format to be inserted in gradle files.
    Args:
        dependency (obj: BuildDependency): The dependency object.

    Returns:
        dependency_string (str): The formatted dependency string.
    """
    # Logic to generate the dependency string based on the dependency type
    if dependency.dep_type == DependencyType.LOCAL_BINARY:
        return """{transitive} (name:'{name}', ext:'{tp}')""".format(
            transitive=TRANSITIVE, name=dependency.name, tp=dependency.bin_type)
    elif dependency.dep_type == DependencyType.LOCAL_MODULE:
        return "{transitive} project(:{name})".format(transitive=TRANSITIVE, name=dependency.name)
    elif dependency.dep_type == DependencyType.CLASSPATH:
        return "classpath '{name}".format(name=dependency.name) + \
               ":{version}'".format(version=dependency.version) if dependency.version is not None else "'"
    else:
        return "{transitive} '{name}".format(transitive=TRANSITIVE, name=dependency.name) + \
               ":{version}'".format(version=dependency.version) if dependency.version is not None else "'"


def set_transitive_names(gradle_plugin_version):
    """Sets the appropriate nomenclature for dependencies based on the Gradle plugin version.
    Args:
        gradle_plugin_version: The Gradle plugin version.
    """
    x = DefaultSemanticVersion(str(gradle_plugin_version))
    # Logic to set the transitive keywords based on the Gradle plugin version
    if x.major < 3:
        global TRANSITIVE
        TRANSITIVE = "compile"
        global TEST_TRANSITIVE
        TEST_TRANSITIVE = "testCompile"
        global ANDROID_TEST_TRANSITIVE
        ANDROID_TEST_TRANSITIVE = "AndroidTestCompile"
        global DEBUG_TRANSITIVE
        DEBUG_TRANSITIVE = "debugCompile"
    # TODO: Decide on the usage of 'api', 'implementation', 'compileOnly', etc. based on Gradle documentation


def is_library_gradle(bld_file):
    """Checks if the given build file is a build file from a library.
    Returns:
        bool: True if it's a library, False otherwise.
    """
    return 'com.android.library' in str(cat(bld_file))


class DummyBuilder(AbstractBuilder):
    """
    Class that extends the functionality of AbstractBuilder to build Gradle projects using a dummy approach.
    This class sets up the Gradle wrapper to build Android Projects.

    Attributes:
        gradle_plg_version (str): The Gradle plugin version for the project.
        build_tools_version (str): The Gradle version for the project.
        retry_on_fail (bool): Whether to retry building when an error occurs.
    """

    def __init__(self, proj, device, resources_dir, instrumenter):
        """
        Initializes a new instance of the DummyBuilder class.

        Args:
            proj: The project object.
            device: The device object.
            resources_dir: The directory containing resources.
            instrumenter: The instrumenter object.
        """
        super(DummyBuilder, self).__init__(proj, device, resources_dir, instrumenter)
        self.gradle_plg_version = proj.get_gradle_plugin()
        self.retry_on_fail = False

    def build_proj_and_apk(self, build_type=BUILD_TYPE.DEBUG, build_tests_apk=False, rebuild=False):
        """
        Builds the project and generates the APK of the specified build type.
        Optionally builds the tests APK and/or rebuilds the project if it was already built.

        Args:
            build_type (BUILD_TYPE): The type of build to perform.
            build_tests_apk (bool): True if the tests' APK has to be generated, False otherwise.
            rebuild (bool): True if the current build has to be cleaned and rebuilt, False otherwise.

        Returns:
            bool: Build results.
        """
        # Logic to perform the build based on the specified parameters
        res = self.build(rebuild=rebuild)  # Build may fail due to release-only tasks
        if build_type == BUILD_TYPE.RELEASE:
            return res and self.build_apk(build_type=build_type) \
                   and self.proj.set_version(build_type) is None \
                   and (True if not build_tests_apk else self.build_tests_apk())
        return self.build_apk(build_type=build_type) \
               and self.proj.set_version(build_type) is None \
               and (True if not build_tests_apk else self.build_tests_apk())

    def install_apks(self, build_type=BUILD_TYPE.DEBUG, install_apk_test=False):
        """
        Installs the APK of the specified build type and optionally the tests' APK.

        Args:
            build_type (BUILD_TYPE): The build type.
            install_apk_test (bool): True if the tests' APK has to be installed, False otherwise.

        Returns:
            apps_list (list): List of installed APKs.
        """
        apps_list = []
        task_name = "install" + build_type.value
        val = self.__execute_gradlew_task(task_name)
        was_success = re.search(BUILD_SUCCESS_VALUE, val)
        if was_success:
            log(f"{task_name}: SUCCESSFUL", log_sev=LogSeverity.SUCCESS)
            app = self.create_app_from_installed_apk(val, build_type)
            apps_list.append(app)
        filename = os.path.join(self.proj.proj_dir, "{task}_{results}.log".format(task=task_name, results=(
            "SUCCESS" if was_success else "ERROR")))
        log_to_file(content=val, filename=filename)
        if install_apk_test:
            task_name = f"install{build_type.value}AndroidTest"
            val = self.__execute_gradlew_task(task_name)
            was_success = re.search(BUILD_SUCCESS_VALUE, val)
            if was_success:
                log(f"{task_name}: SUCCESSFUL", log_sev=LogSeverity.SUCCESS)
            filename = os.path.join(self.proj.proj_dir, "{task}_{results}.log".format(task=task_name, results=(
                "SUCCESS" if was_success else "ERROR")))
            log_to_file(content=val, filename=filename)
        return apps_list

    def uninstall_all_apks(self):
        """uninstall all project apks."""
        task_name = "uninstallAll"
        self.__execute_gradlew_task(task_name)

    def create_app_from_installed_apk(self, gradle_output, build_type):
        """create App object from installed apk on device.
		Args:
		    gradle_output: build output.
			build_type: build type.
		Returns:
			app(App): created app.
		"""
        installed_apk_simple_name = re.search(r"Installing APK \'(.*?)\'", gradle_output).groups()[0]
        full_apk_path = next(
            filter(lambda x: str(x).endswith(installed_apk_simple_name), self.proj.get_apks(build_type=build_type)),
            self.proj.get_apks(build_type=build_type)[0])
        new_pkgs = self.device.get_new_installed_pkgs()
        if len(new_pkgs) == 0:
            # app was already installed
            log("app already installed", log_sev=LogSeverity.INFO)
            app_pack = self.device.get_package_matching(self.proj.pkg_name)
            new_pkgs.append(app_pack)
        apk_pkg = new_pkgs[-1]  # ASSUMING JUST ONE
        app = App(self.device, self.proj, apk_pkg, apk_path=full_apk_path, local_res_dir=self.proj.results_dir)
        return app

    def sign_apks(self, build_type=BUILD_TYPE.DEBUG):
        """Sign project apks of build_type.
		Args:
			build_type: build type.

		Returns:
			bool: True if success, False otherwise.
		"""
        if self.was_last_build_successful(task="sign") or build_type == BUILD_TYPE.DEBUG:
            return True
        for apk_path in self.proj.get_apks(build_type):
            ret, o, e = sign_apk(apk_path)
            if ret == 0 and len(e) < 3:
                log("APK Successfully signed", log_sev=LogSeverity.SUCCESS)
                return True
            else:
                loge(f"Error signing apk {apk_path} {e}")
                return False

    def build_apk(self, build_type=BUILD_TYPE.DEBUG):
        """Build apk of build_type.
		Args:
			build_type: build type.

		Returns:
			bool: True if success, False otherwise.
		"""
        task = f"assemble{build_type.value}"
        if self.was_last_build_successful(task) and not self.needs_rebuild():
            log(f"Not building again {build_type}. Last build was successful", log_sev=LogSeverity.INFO)
            return True
        apks_built = self.proj.get_apks()
        val = self.__execute_gradlew_task(task=task)
        was_success = BUILD_SUCCESS_VALUE in val
        if was_success:
            log(f"BUILD ({build_type.value}) SUCCESSFUL", log_sev=LogSeverity.SUCCESS)
            self.regist_successful_build(task)
            apks_now = self.proj.get_apks()
            fresh_apks = [x for x in apks_now if x not in apks_built]
            for apk in fresh_apks:
                if build_type == BUILD_TYPE.RELEASE:
                    sign_apk(apk)
                self.proj.add_apk(apk, build_type)
        else:
            log("Error Building APK", log_sev=LogSeverity.ERROR)
            self.regist_error_build(task)
            return False
        return True

    def build_tests_apk(self):
        """builds tests apk.
		Returns:
			bool: True if success, False otherwise.
		"""
        task = "assembleAndroidTest"
        if self.was_last_build_successful(task) and not self.needs_rebuild():
            log("Not building again. Last build was successful", log_sev=LogSeverity.WARNING)
            return True
        apks_built = self.proj.get_apks()
        val = self.__execute_gradlew_task(task=task)
        was_success = str(val | grep(BUILD_SUCCESS_VALUE)) != ""
        if was_success:
            log(f"{task}: SUCCESSFUL", log_sev=LogSeverity.SUCCESS)
            self.regist_successful_build(task)
            apks_now = self.proj.get_apks()
            apks_test = [x for x in apks_now if x not in apks_built]
            for apks_test in apks_test:
                self.proj.add_apk(apks_test, None)
        else:
            log("Error Building test APK", log_sev=LogSeverity.ERROR)
            self.regist_error_build(task)
            return False
        return True

    def build(self, rebuild=False):
        """builds project if project is not build yet or rebuild is True.
		Args:
			rebuild: True if the project has to be rebuilt.

		Returns:
			bool: True if success, False otherwise.
		"""
        build_was_succcessful = self.was_last_build_successful()
        if build_was_succcessful and not rebuild:
            log("Not building again. Last build was successful", log_sev=LogSeverity.INFO)
            return True

        if not self.retry_on_fail and not build_was_succcessful and self.was_attempted_to_build_before():
            log("Skipping failed build. Retry on failed flag is disabled", log_sev=LogSeverity.ERROR)
            return True

        self.__execute_gradlew_task("clean")  # mainly to ensure that built apks from original proj do not persist
        for mod_name, proj_module in self.proj.modules.items():
            bld_file = proj_module.build_file
            self.__set_build_tools_version(bld_file)
            self.__add_or_update_dexoptions(bld_file)
            self.__add_or_update_lintoptions(bld_file)
            self.__add_plugins(bld_file)
            self.needs_min_sdk_upgrade(bld_file)
            self.adapt_target_sdk_upgrade(bld_file)
            self.__update_test_instrumentation_runner(bld_file)
            self.__add_external_libs_fldr(proj_module)
            self.__add_external_libs(proj_module)
        # maybe change build tools?
        self.__add_build_classpaths()
        self.__add_external_libs_to_repositories()
        self.__add_or_replace_local_properties_files()
        return self.build_with_gradlew(self.get_config("build_fail_retries", DEFAULT_BUILD_TIMES_TO_TRY),
                                       skip_lint=True)

    def build_with_gradlew(self, tries=DEFAULT_BUILD_TIMES_TO_TRY, target_task="build", skip_lint=False):
        """performs build task with gradle.
		Args:
			tries: number max of tries to fix build errors.
			target_task: task to perform.

		Returns:
			bool: True if success, False otherwise.
		"""
        has_gradle_wrapper = self.proj.has_gradle_wrapper()
        if not has_gradle_wrapper:
            # create gradle wrapper
            copy(os.path.join(self.resources_dir, "build", "gradle", "gradlew"), self.proj.proj_dir)
        lint_option_cmd = " -x lint" if skip_lint else ""
        val = self.__execute_gradlew_task(target_task + lint_option_cmd)
        was_success = BUILD_SUCCESS_VALUE in val
        if was_success:
            log(f"{target_task}: BUILD SUCCESSFUL", log_sev=LogSeverity.SUCCESS)
            self.regist_successful_build(target_task)
            return True
        else:
            error = is_known_error(val)
            if error is not None and tries > 0:
                # solve_known_error(self.proj, error, error_msg=val, **{'build-tools': self.build_tools_version})
                log(f"{target_task}: BUILD FAILED. error is known ({error})", log_sev=LogSeverity.WARNING)
                log_to_file(f"{error}", os.path.join(self.proj.proj_dir, "registered_errors.log"))
                return self.build_with_gradlew(tries=tries - 1, target_task=target_task)
            else:
                if error is not None:
                    log(f"{target_task}: BUILD FAILED. error is known ({error})", log_sev=LogSeverity.WARNING)
                loge("Unable to solve Building error")
                self.regist_error_build(target_task)
                log_to_file(f"{val}\n-------", os.path.join(self.proj.proj_dir, "unknown_errors.log"))
                return False

    def __execute_gradlew_task(self, task):
        """execute gradle task with gradle wrapper.
        Args:
			task: task name.

		Returns:
			str: command output.
		"""
        log(f"Executing Gradle task: {task}", log_sev=LogSeverity.INFO)
        build_timeout_val = self.get_config("build_timeout", None)
        build_timeout_val = None if build_timeout_val == 0 else build_timeout_val
        # build_timeout = f'gtimeout  -s 9 {build_timeout_val}' if build_timeout_val > 0 else ""
        # print(build_timeout)
        cmd = "cd {projdir}; chmod +x gradlew ; ./gradlew {task}".format(
            projdir=self.proj.proj_dir, task=task, build_timeout=build_timeout_val)
        res = execute_shell_command(cmd, timeout=build_timeout_val)
        if res.validate("error running gradle task"):
            return res.output
        else:
            return res.errors

    def needs_min_sdk_upgrade(self, gradle_file):
        return False

    def adapt_target_sdk_upgrade(self, gradle_file):
        pass

    def __add_or_update_dexoptions(self, gradle_file):
        """Adds dexoptions to build file if needed.
		Args:
			gradle_file: gradle file.
		"""
        pass

    def __add_or_update_lintoptions(self, gradle_file):
        """Adds lint options.
		"""
        pass

    def __update_test_instrumentation_runner(self, gradle_file):
        """Updates test runner according to device sdk version.
		Args:
			gradle_file: gradle file
		"""
        pass

    def __filter_opts(self, opts, excluding_set):
        to_keep = {}
        try:
            for dex_op in opts:
                opt_tpls = re.search(r'(.*?)(=|\s|:)([^{}]+)', dex_op.strip()).groups()
                opt_key = opt_tpls[0].strip()
                opt_oper = opt_tpls[1]
                opt_val = opt_tpls[2].strip()
                if opt_key not in excluding_set:
                    to_keep[opt_key] = (opt_oper, opt_val)
                else:
                    print("Removed or replaced opt %s" % opt_key)
        except:
            loge("error filtering opts in gradle file")
            return opts
        return to_keep

    def __add_or_replace_local_properties_files(self):
        pass

    def build_local_properties_file(self):
        """builds local.properties file content.
		Returns:
			str: file content.
		"""
        return '''
				sdk.dir={android_home}
				sdk-location={android_home}
				ndk.dir={android_home}/ndk-bundle
				ndk-location={android_home}/ndk-bundle''' \
            .format(android_home=self.android_home_dir)

    def __add_external_libs_to_repositories(self):
        pass

    def __add_external_libs_fldr(self, proj_module):
        """adds folder to include local 3rd party libs.
		Args:
			proj_module(obj:ProjectModule): project module.
		"""
        pass

    def __add_external_libs(self, proj_module):
        """adds dependencies to module.
		Args:
			proj_module(obj:ProjectModule): project module.
		"""
        pass

    def needs_external_lib_dependency(self):
        """needs build dependencies from instrumenter.
		Returns:
			bool: True if needs, False otherwise.
		"""
        return False

    def was_last_build_successful(self, task="build"):
        """checks if last build attempt was successful.
		inspects BUILD_RESULTS_FILE file and checks build result.
		Returns:
			bool: True if build was successful, False otherwise.
		"""
        filename = os.path.join(self.proj.proj_dir, BUILD_RESULTS_FILE)
        if os.path.exists(filename):
            with open(filename, 'r') as fl:
                js = json.load(fl)
            return js[task].lower() == SUCCESS_VALUE.lower() if task in js else False
        return False

    def regist_successful_build(self, task="build"):
        """record successful build in file.
		Args:
			task: build task name.
		"""
        filename = os.path.join(self.proj.proj_dir, BUILD_RESULTS_FILE)
        js = {}
        if os.path.exists(filename):
            with open(filename, 'r') as fl:
                js = json.load(fl)

        js[task] = SUCCESS_VALUE
        with open(filename, 'w') as outfile:
            json.dump(js, outfile)

    def regist_error_build(self, task="build"):
        """record successful build in file.
		Args:
			task: build task name.
		"""
        filename = os.path.join(self.proj.proj_dir, BUILD_RESULTS_FILE)
        js = {}
        if os.path.exists(filename):
            with open(filename, 'r') as fl:
                js = json.load(fl)

        js[task] = ERROR_VALUE
        with open(filename, 'w') as outfile:
            json.dump(js, outfile)

    def __set_build_tools_version(self, bld_file, btools_version=DEFAULT_BUILD_TOOLS_VERSION):
        pass

    def __add_plugins(self, bld_file):
        pass

    def __add_build_classpaths(self):
        """adds build dependencies of the instrumenter if needed."""
        pass

    def __has_built_apks(self):
        """checks if project has apks already built.
		Returns:
			bool: True if has, False otherwise.
		"""
        return len(mega_find(self.proj.proj_dir, pattern="*.apk", type_file='f')) > 0

    def needs_rebuild(self):
        """checks if project needs rebuild.
		Returns:
			bool: True if needs, False otherwise.
		"""
        return not self.__has_built_apks()  # TODO check build type and maybe last build output, lint, etc

    def was_attempted_to_build_before(self):
        """checks if there was a build attempt before.
		Returns:
			bool: True if yes, False otherwise.
		"""
        filename = os.path.join(self.proj.proj_dir, BUILD_RESULTS_FILE)
        return os.path.exists(filename)
