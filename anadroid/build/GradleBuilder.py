import os
from shutil import copy

from textops import grep, cat, sed, head, echo
import json
import re

from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.application.Application import App
from anadroid.application.Dependency import DependencyType
from anadroid.build.AbstractBuilder import AbstractBuilder
from anadroid.build.versionUpgrader import DefaultSemanticVersion, can_be_semantic_version
from anadroid.device.MockedDevice import MockedDevice
from anadroid.utils.Utils import mega_find, execute_shell_command, sign_apk, log_to_file, loge, logw, logs, logi
from anadroid.build.GracleBuildErrorSolver import is_known_error, solve_known_error

TRANSITIVE = "implementation"
TEST_TRANSITIVE = "testImplementation"
ANDROID_TEST_TRANSITIVE = "androidTestImplementation"
DEBUG_TRANSITIVE = "debugImplementation"

TEST_RUNNERS = {
	'android.test.InstrumentationTestRunner': 22,
	'android.support.test.runner.AndroidJUnitRunner': 28,
	'androidx.test.runner.AndroidJUnitRunner': 32
}

LOCAL_PROPERTIES_FLAGS = {
	'android.enableBuildCache': 'true',
	'org.gradle.caching': 'true',
}

LINT_ISSUES = {
	'Recycle', 'Wakelock', 'DrawAllocation',
	'ObsoleteLayoutParam', 'ViewHolder'}

DEX_OPTIONS = {
	'preDexLibraries': 'false',
	'javaMaxHeapSize': '"8g"'
}

LINT_OPTIONS = {
	'abortOnError': 'false',
}

ATTRIBS_NAME_REMAPS = {
	'packageName': 'applicationId',
	'testPackageName': 'testApplicationId',
	'packageNameSuffix': 'applicationIdSuffix',
	'android.plugin.bootClasspath': 'android.bootClasspath',
	'android.plugin.ndkFolder': 'android.plugin.ndkDirectory ',
	'zipAlign': 'zipAlignEnabled',
	'jniDebugBuild': 'jniDebuggable',
	'renderscriptDebug': 'renderscriptDebuggable',
	'flavorGroups': 'flavorDimensions',
	'renderscriptSupportMode': 'renderscriptSupportModeEnabled',
	'ProductFlavor.renderscriptNdkMode': 'renderscriptNdkModeEnabled',
	'InstrumentTest': 'androidTest',
	'instrumentTestCompile': 'jniDebuggable',
}

BUILD_RESULTS_FILE = "buildStatus.json"
SUCCESS_VALUE = "Success"
ERROR_VALUE = "Error"
BUILD_SUCCESS_VALUE = "BUILD SUCCESSFUL"
DEFAULT_BUILD_TIMES_TO_TRY = 5
DEFAULT_BUILD_TOOLS_VERSION = '25.0.3'# TODO


def gen_dependency_string(dependency):
	"""generates dependency format to be inserted in gradle files.
	Args:
		dependency(obj: `BuildDependency`): dependency.

	Returns:
		dependency_string(str): dependency format as string.
	"""
	if dependency.dep_type == DependencyType.LOCAL_BINARY:
		return """{transitive} (name:'{name}', ext:'{tp}')""".format(transitive=TRANSITIVE, name=dependency.name,
																	 tp=dependency.bin_type)
	elif dependency.dep_type == DependencyType.LOCAL_MODULE:
		return "{transitive} project(:{name})".format(transitive=TRANSITIVE, name=dependency.name)
	elif dependency.dep_type == DependencyType.CLASSPATH:
		return "classpath '{name}".format(name=dependency.name) \
			   + ":{version}'".format(version=dependency.version) if dependency.version is not None else "'"
	else:
		return "{transitive} '{name}".format(transitive=TRANSITIVE, name=dependency.name) \
			   + ":{version}'".format(version=dependency.version) if dependency.version is not None else "'"


def set_transitive_names(gradle_plugin_version):
	"""Given the gradle-plugin version, sets the most adequate nomenclature to use in dependencies definition.
	Args:
		gradle_plugin_version: gradle-plugin version.
	"""
	x = DefaultSemanticVersion(str(gradle_plugin_version))
	if x.major < 3:
		global TRANSITIVE
		TRANSITIVE = "compile"
		global TEST_TRANSITIVE
		TEST_TRANSITIVE = "testCompile"
		global ANDROID_TEST_TRANSITIVE
		ANDROID_TEST_TRANSITIVE = "AndroidTestCompile"
		global DEBUG_TRANSITIVE
		DEBUG_TRANSITIVE = "debugCompile"
		# TODO api vs implementation vs compilonly ... https://developer.android.com/studio/build/dependencies#dependency_configurations


def is_library_gradle(bld_file):
	"""checks if bld_file is a build file from a library.
	Returns:
		bool: True if is a library, False otherwise.
	"""
	return 'com.android.library' in str(cat(bld_file))


class GradleBuilder(AbstractBuilder):
	"""Class that extends AbstractBuilder functionality in order to build Gradle projects.
	Attributes:
		build_flags(dict): build flags.
		change_history(list): list of changes performed to project.
		gradle_plg_version(str): Gradle plugin version for proj.
		build_tools_version(str): Gradle version for proj.
	"""
	def __init__(self, proj, device, resources_dir, instrumenter):
		super(GradleBuilder, self).__init__(proj, device, resources_dir, instrumenter)
		self.build_flags = {}
		self.change_history = []
		self.gradle_plg_version = proj.get_gradle_plugin()
		self.build_tools_version = None
		set_transitive_names(self.gradle_plg_version)
		self.retry_on_fail = self.get_config("retry_failed", True)

	def build_proj_and_apk(self, build_type=BUILD_TYPE.DEBUG, build_tests_apk=False, rebuild=False):
		"""builds project and generates apk of build type. It can optionally build the tests apk and/or rebuild
		the current project in case it was already built.
		Args:
			build_type(BUILD_TYPE): type of build to perform.
			build_tests_apk(bool): True if the tests' apk has to be generated, False otherwise.
			rebuild(bool): True if the current build has to be cleaned and rebuilt, False otherwise.

		Returns:
			bool: build results.
		"""
		res = self.build(rebuild=rebuild) # might fail because of release only tasks
		if build_type == BUILD_TYPE.RELEASE:
			return res and self.build_apk(build_type=build_type) \
				   and self.proj.set_version(build_type) is None \
				   and (True if not build_tests_apk else self.build_tests_apk())
		return self.build_apk(build_type=build_type) \
			   and self.proj.set_version(build_type) is None \
			   and (True if not build_tests_apk else self.build_tests_apk())

	def install_apks(self, build_type=BUILD_TYPE.DEBUG, install_apk_test=False):
		"""install apk of build_type and optionally de tests apk.
		Args:
			build_type(BUILD_TYPE): build type.
			install_apk_test(bool): True if the tests' apk has to be installed, False otherwise.

		Returns:
			apps_list(list): list of installed apks.
		"""
		# TODO background installer
		apps_list = []
		task_name = "install" + build_type.value
		val = self.__execute_gradlew_task(task_name)
		was_success = re.search(BUILD_SUCCESS_VALUE, val)
		if was_success:
			logs(f"{task_name}: SUCCESSFUL")
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
				logs(f"{task_name}: SUCCESSFUL")
			filename = os.path.join(self.proj.proj_dir, "{task}_{results}.log".format(task=task_name, results=(
				"SUCCESS" if was_success else "ERROR")))
			log_to_file(content=val, filename=filename)
		return apps_list

	def uninstall_all_apks(self):
		"""uninstall all project apks."""
		if isinstance(self.device, MockedDevice):
			return
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
			logi("app already installed")
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
				logs("APK Successfully signed")
				return True
			else:
				loge(f"Error signing apk {apk_path} {e}")
				print(e)
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
			logi(f"Not building again {build_type}. Last build was successful")
			return True
		apks_built = self.proj.get_apks()
		val = self.__execute_gradlew_task(task=task)
		was_success = BUILD_SUCCESS_VALUE in val
		if was_success:
			logs(f"BUILD ({build_type.value}) SUCCESSFUL")
			self.regist_successful_build(task)
			apks_now = self.proj.get_apks(build_type=build_type)
			fresh_apks = [x for x in apks_now if x not in apks_built]
			for apk in fresh_apks:
				if build_type == BUILD_TYPE.RELEASE:
					sign_apk(apk)
				self.proj.add_apk(apk, build_type)
		else:
			loge("Error Building APK")
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
			logw("Not building again. Last build was successful")
			return True
		apks_built = self.proj.get_apks()
		val = self.__execute_gradlew_task(task=task)
		was_success = str(val | grep(BUILD_SUCCESS_VALUE)) != ""
		if was_success:
			logs(f"{task}: SUCCESSFUL")
			self.regist_successful_build(task)
			apks_now = self.proj.get_apks()
			apks_test = [x for x in apks_now if x not in apks_built]
			for apks_test in apks_test:
				self.proj.add_apk(apks_test, None)
		else:
			loge("Error Building test APK")
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
			logi("Not building again. Last build was successful")
			return True

		if not self.retry_on_fail and not build_was_succcessful and self.was_attempted_to_build_before():
			logw("Skipping failed build. Retry on failed flag is disabled")
			return True

		self.__execute_gradlew_task("clean") # mainly to ensure that built apks from original proj do not persist
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
		return self.build_with_gradlew(self.get_config("build_fail_retries", DEFAULT_BUILD_TIMES_TO_TRY), skip_lint=True)

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
		val = self.__execute_gradlew_task(target_task + lint_option_cmd  + " -x test")
		was_success = BUILD_SUCCESS_VALUE in val
		if was_success:
			logs(f"{target_task}: BUILD SUCCESSFUL")
			self.regist_successful_build(target_task)
			return True
		else:
			error = is_known_error(val)
			if error is not None and tries > 0:
				solve_known_error(self.proj, error, error_msg=val, **{'build-tools': self.build_tools_version})
				loge(f"{target_task}: BUILD FAILED. error is known ({error}). Fixing error and retrying")
				log_to_file(f"{error}", os.path.join(self.proj.proj_dir, "registered_errors.log"))
				return self.build_with_gradlew(tries=tries - 1, target_task=target_task)
			else:
				print(val)
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
		logi(f"Executing Gradle task: {task}")
		build_timeout_val = self.get_config("build_timeout", None)
		build_timeout_val = None if build_timeout_val == 0 else build_timeout_val
		#build_timeout = f'gtimeout  -s 9 {build_timeout_val}' if build_timeout_val > 0 else ""
		#print(build_timeout)
		cmd = "cd {projdir}; chmod +x gradlew ; ./gradlew {task}".format(
				projdir=self.proj.proj_dir, task=task, build_timeout=build_timeout_val)
		res = execute_shell_command(cmd, timeout=build_timeout_val)
		if res.validate(f"error running gradle task ({task})"):
			return res.output
		else:
			return res.errors

	def needs_min_sdk_upgrade(self, gradle_file):
		"""infers if module needs min sdk upgrade in order to the app be installed on the current device.
		Args:
			gradle_file: gradle file.
		"""
		has_min_sdk = cat(gradle_file) | grep(r'minSdkVersion.*[0-9]+')
		if str(has_min_sdk) != "":
			min_sdk = has_min_sdk | sed('minSdkVersion| |=|\n', "") | head(1)
			device_sdk_version = self.device.get_device_sdk_version()
			if int(str(min_sdk)) > device_sdk_version:
				logw(f"This app target sdk version {min_sdk}. This is greater than the device version and the application"
					f" might not work properly on the connected device")
				new_file = re.sub(r'minSdkVersion (.+)', r'minSdkVersion %d' % device_sdk_version,
								  str(cat(gradle_file)))
				with open(gradle_file, 'w') as u:
					u.write(new_file)
				return True
		return False

	def adapt_target_sdk_upgrade(self, gradle_file):
		"""Adapts target sdk upgrade to connected device if needed.
		Args:
			gradle_file: gradle file.
		"""
		has_target_sdk = cat(gradle_file) | grep(r'targetSdkVersion.*[0-9]+')
		if str(has_target_sdk) != "":
			device_target_sdk_version = self.device.get_device_sdk_version()
			new_file = re.sub(r'targetSdkVersion (.+)', r'targetSdkVersion %d' % device_target_sdk_version,
							  str(cat(gradle_file)))
			with open(gradle_file, 'w') as u:
				u.write(new_file)
			return True
		return False

	def __add_or_update_dexoptions(self, gradle_file):
		"""Adds dexoptions to build file if needed.
		Args:
			gradle_file: gradle file.
		"""
		new_dex_opts = {}
		file_ctent = str(cat(gradle_file))
		#has_android = re.search(r'android.*?\{', file_ctent)
		has_android = re.search(r'android[^\w]*?\{', file_ctent)
		if has_android is None:
			return
		has_dex_options = re.search(r'dexOptions.*?\{', file_ctent)
		if has_dex_options is not None:
			original_dex_options = re.search(r'dexOptions.*?\{([^}]+)', file_ctent).groups()[0].strip().split("\n")
			new_dex_opts = self.__filter_opts(original_dex_options, DEX_OPTIONS.keys())
			for dx, dval in DEX_OPTIONS.items():
				new_dex_opts[dx] = (" ", dval)
		else:
			for dx, dval in DEX_OPTIONS.items():
				new_dex_opts[dx] = (" ", dval)
		# build string for adding to dexoptions
		line = ""
		for a, b in new_dex_opts.items():
			line += "\t\t%s%s%s\n" % (a, b[0], b[1])
		line = "android {\n\tdexOptions {\n%s\t}" % line
		fl_without_dexopts = re.sub(r'dexOptions.*?\{([^{}]+)}', "", file_ctent)
		fl_ok = re.sub(r'android[^\w]*?\{', line, fl_without_dexopts)
		with open(gradle_file, 'w') as u:
			u.write(fl_ok)

	def __add_or_update_lintoptions(self, gradle_file):
		"""Adds lint options.
		"""
		new_lint_opts = {}
		file_ctent = str(cat(gradle_file))
		has_android = re.search(r'android[^\w]*?\{', file_ctent)
		if has_android is None:
			return
		has_lint_options = re.search(r'lintOptions.*?\{', file_ctent)
		if has_lint_options is not None:
			original_lint_options = re.search(r'lintOptions.*?\{([^{}]+)}', file_ctent).groups()[0].strip().split("\n")
			new_lint_opts = self.__filter_opts(original_lint_options, LINT_OPTIONS.keys())
			for dx, dval in LINT_OPTIONS.items():
				new_lint_opts[dx] = (" ", dval)
		else:
			for dx, dval in LINT_OPTIONS.items():
				new_lint_opts[dx] = (" ", dval)
		# build string for adding to dexoptions
		line = ""
		for a, b in new_lint_opts.items():
			line += "\t\t%s%s%s\n" % (a, b[0], b[1])
		line = "android {\n\tlintOptions {\n%s\t}" % line
		fl_without_dexopts = re.sub(r'lintOptions.*?\{([^{}]+)}', "", file_ctent)
		fl_ok = re.sub(r'android[^\w]*?\{', line, fl_without_dexopts)
		with open(gradle_file, 'w') as u:
			u.write(fl_ok)

	def __update_test_instrumentation_runner(self, gradle_file):
		"""Updates test runner according to device sdk version.
		Args:
			gradle_file: gradle file
		"""
		file_ctent = str(cat(gradle_file))
		has_inst_runner = re.search(r'testInstrumentationRunner', file_ctent)
		if has_inst_runner is None:
			return
		contains_androidx_dependency = re.search(r'androidx\.test\.*', file_ctent)
		device_sdk = self.device.get_device_sdk_version() if contains_androidx_dependency is None else 100
		adequate_test_runner = list(filter(lambda x: x[1] <= device_sdk, TEST_RUNNERS.items()))[-1]
		new_file = re.sub(r"testInstrumentationRunner (.+)",
						  r"testInstrumentationRunner '%s'" % adequate_test_runner[0], file_ctent)
		with open(gradle_file, 'w') as u:
			u.write(new_file)

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
					self.change_history.append("Removed or replaced opt %s" % opt_key)
		except:
			loge("error filtering opts in gradle file")
			return opts
		return to_keep

	def __add_or_replace_local_properties_files(self):
		"""Update or create local.properties file.
		"""
		local_props_files = mega_find(self.proj.proj_dir, pattern="local.properties", maxdepth=3)
		custom_prop_file_ctent = self.build_local_properties_file()
		for loc_prop in local_props_files:
			with open(loc_prop, 'w') as u:
				u.write(custom_prop_file_ctent)
				u.close()

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
		if self.needs_external_lib_dependency():
			file_ctent = str(cat(self.proj.root_build_file))
			new_file = file_ctent + "\nallprojects {repositories {flatDir { dirs 'libs'}}}"
			with open(self.proj.root_build_file, 'w') as u:
				u.write(new_file)

	def __add_external_libs_fldr(self, proj_module):
		"""adds folder to include local 3rd party libs.
		Args:
			proj_module(obj:ProjectModule): project module.
		"""
		bld_file = proj_module.build_file
		if bld_file == self.proj.root_build_file:
			return

		if self.instrumenter.profiler.needs_external_dependencies():
			# create folder
			created_dir = proj_module.create_inner_folder(name="libs")
			# copy external lib to folder
			lib_filepath = self.instrumenter.profiler.local_dep_location
			copy(lib_filepath, created_dir)

	def __add_external_libs(self, proj_module):
		"""adds dependencies to module.
		Args:
			proj_module(obj:ProjectModule): project module.
		"""
		bld_file = proj_module.build_file
		if not self.needs_external_lib_dependency():
			return
		file_ctent = str(cat(bld_file))
		dependencies = self.instrumenter.get_build_dependencies()
		#has_depts = re.search(r'dependencies.*?\{(.|\n)*}', file_ctent).group(0)
		new_deps="\ndependencies{\n\t"
		for n_dp in dependencies:
			new_deps += gen_dependency_string(n_dp) + "\n\t"
		new_file_ctent = file_ctent + new_deps + "}\n"
		with open(bld_file, 'w') as u:
			u.write(new_file_ctent)

	def needs_external_lib_dependency(self):
		"""needs build dependencies from instrumenter.
		Returns:
			bool: True if needs, False otherwise.
		"""
		return self.instrumenter.needs_build_dependency()

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
		"""sets build tools version btools_version on bld_file.
		Args:
			bld_file: build file.
			btools_version: version.
		"""
		has_bld_tools = str((cat(bld_file) | grep("buildToolsVersion") | sed("buildToolsVersion|\"", ""))).strip()
		if has_bld_tools != "":
			if can_be_semantic_version(has_bld_tools):
				self.build_tools_version = DefaultSemanticVersion(has_bld_tools)
				return
			elif "ext." in has_bld_tools:
				var_name = has_bld_tools.split("ext.")[-1]
				target_pattern1, target_pattern2 = r'ext.*?\{', r'%s.*?=.*' % var_name
				x = list(filter(lambda t: re.search(target_pattern1, str(cat(t))) and re.search(target_pattern2, str(cat(t))), mega_find(self.proj.proj_dir, "*.gradle", type_file='f')))
				if len(x) > 0:
					# assume 0
					pattern = re.sub(r'\"|\'', "", re.search(target_pattern2, str(cat(x[0]))).group().split("=")[1].strip())
					if can_be_semantic_version(pattern):
						self.build_tools_version = DefaultSemanticVersion(pattern)
						return
			else:
				logw(f"unable to determinate build tools version. Using default: {btools_version}")
				self.build_tools_version = DefaultSemanticVersion(btools_version)

	def __add_plugins(self, bld_file):
		"""adds build plugins if needed
		Args:
			bld_file: build file.
		"""
		if not self.instrumenter.needs_build_plugin():
			return
		file_content = str(cat(bld_file))
		plugins = self.instrumenter.get_build_plugins()
		if len(plugins) > 0 and plugins[0] in file_content:

			return
		has_plugin_apply = re.search(r'apply.*plugin.*', file_content)
		plg_string = ""
		if has_plugin_apply:
			# replace
			# plgs = echo(file_content) | grep(r'apply.*plugin')
			# it can't be the first plugin
			plgs = re.findall(r'apply.*plugin.*', file_content)
			for plg in plugins:
				if 'hunter' in plg and is_library_gradle(bld_file):
					continue
				plg_string += f"apply plugin: '{plg}'\n"
			# file_content = re.sub(plgs, (plg_string + plgs), file_content)
			last_plg = plgs[len(plgs) - 1]
			new_plgs = last_plg + "\n" + plg_string
			file_content = file_content.replace(last_plg, new_plgs)
		else:
			has_plugins = re.search(r'plugins.*\{', file_content)
			if has_plugins:
				original_plugs = re.search(r'plugins.*?\{([^{}]+)}', file_content).groups()[0]
				for plg in plugins:
					plg_string += f"\tid '{plg}'\n"
				file_content = re.sub(original_plugs, original_plugs + plg_string, file_content)
			else:
				# append at beginning
				for plg in plugins:
					plg_string += f"apply plugin: '{plg}'\n"
				file_content = plg_string + file_content
		with open(bld_file, 'w') as u:
			u.write(file_content)

	def __add_build_classpaths(self):
		"""adds build dependencies of the instrumenter if needed."""
		if not self.instrumenter.needs_build_classpaths():
			return
		file_ctent = str(cat(self.proj.root_build_file))
		# TODO: more elegant way to do this, instead of just appending to build file
		classpaths = self.instrumenter.get_build_classpaths()
		pato_str = "buildscript{\n\tdependencies{\n"
		for pato in classpaths:
			pato_str += gen_dependency_string(pato) + "\n"
		new_file_ctnt = file_ctent + "\n" + pato_str + "\n}\n}"
		with open(self.proj.root_build_file, 'w') as u:
			u.write(new_file_ctnt)

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

