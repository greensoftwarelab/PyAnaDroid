import os
from shutil import copy

from textops import grep, cat, sed, head, echo
import json
import re

from src.application.AndroidProject import BUILD_TYPE
from src.application.Dependency import DependencyType
from src.build.AbstractBuilder import AbstractBuilder
from src.build.versionUpgrader import DefaultSemanticVersion
from src.utils.Utils import mega_find, execute_shell_command, sign_apk
from src.build.GracleBuildErrorSolver import is_known_error, solve_known_error

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
    'javaMaxHeapSize': '"4g"'
}

LINT_OPTIONS = {
    'abortOnError': 'false',
}

ATRIBS_NAME_REMAPS = {
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


def gen_dependency_string(dependency):
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


class GradleBuilder(AbstractBuilder):
    def __init__(self, proj, device, resources_dir, instrumenter):
        super(GradleBuilder, self).__init__(proj, device, resources_dir, instrumenter)
        self.build_flags = {}
        self.change_history = []
        self.gradle_plg_version = proj.get_gradle_plugin()
        self.build_tools_version = None
        set_transitive_names(self.gradle_plg_version)

    def build_proj_and_apk(self, build_type=BUILD_TYPE.DEBUG):
        self.build()
        self.build_apk(build_type=build_type)
        self.proj.set_version(build_type)

    def sign_apks(self, build_type=BUILD_TYPE.DEBUG):
        if self.was_last_build_successful(task="sign") or build_type == BUILD_TYPE.DEBUG:
            return
        print("signing generated apks")
        for apk_path in self.proj.get_apks(build_type):
            ret, o, e = sign_apk(apk_path)
            if ret == 0 and len(e) < 3:
                print("APK Successfully signed")
            else:
                raise Exception("Error signing apk")

    def build_apk(self, build_type=BUILD_TYPE.DEBUG):
        task = "assemble" + build_type.value
        if self.was_last_build_successful(task) and not self.needs_rebuild():
            print("Not building again. Last build was successful")
            return
        val = self.__execute_gradlew_task(task=task)
        was_success = str(val | grep("BUILD SUCCESSFUL")) != ""
        if was_success:
            print("BUILD SUCCESSFUL")
            self.regist_successfull_build(task)
            if build_type == BUILD_TYPE.RELEASE:
                res = self.proj.get_apks(build_type=BUILD_TYPE.RELEASE)
                for apk in res:
                    print("signing")
                    sign_apk(apk)
        else:
            print("Error Building APK")

    def build_tests_apk(self):
        pass

    def build(self):
        if self.was_last_build_successful():
            print("Not building again. Last build was successfull")
            return
        for mod_name, proj_module in self.proj.modules.items():
            bld_file = proj_module.build_file
            self.__set_build_tools_version(bld_file)
            self.__add_or_update_dexoptions(bld_file)
            self.__add_or_update_lintoptions(bld_file)
            self.__add_plugins(bld_file)
            self.needs_min_sdk_upgrade(bld_file)
            self.needs_target_sdk_upgrade(bld_file)
            self.__update_test_instrumentation_runner(bld_file)
            self.__add_external_libs_fldr(proj_module)
            self.__add_external_libs(proj_module)
            # maybe change build tools?
        self.__add_build_classpaths()
        self.__add_external_libs_to_repositories()
        self.__add_or_replace_local_properties_files()
        self.build_with_gradlew()

    def build_with_gradlew(self, tries=5, target_task="build"):
        has_gradle_wrapper = self.proj.has_gradle_wrapper()
        if not has_gradle_wrapper:
            # create gradle wrapper
            copy(self.resources_dir + "/build/gradle/gradlew", self.proj.proj_dir)
        val = self.__execute_gradlew_task(target_task)
        was_success = str(val | grep("BUILD SUCCESSFUL")) != ""
        if was_success:
            print("BUILD SUCCESSFUL")
            self.regist_successfull_build(target_task)
        else:
            error = is_known_error(val)
            if error is not None and tries > 0:
                solve_known_error(error, self.proj)
                print("BUILD FAILED. Retrying")
                self.build_with_gradlew(tries=tries - 1, target_task=target_task)
            else:
                raise Exception("Unable to solve Building error")

    def __execute_gradlew_task(self, task):
        print("TASK:")
        print(task)
        res = execute_shell_command(
            "cd {projdir}; chmod +x gradlew ;./gradlew {task}".format(projdir=self.proj.proj_dir, task=task))
        if res.validate(Exception("error running gradle task")):
            return res.output
        else:
            return res.errors

    def needs_min_sdk_upgrade(self, gradle_file):
        has_min_sdk = cat(gradle_file) | grep(r'minSdkVersion.*[0-9]+')
        # has_min_sdk =
        if str(has_min_sdk) != "":
            min_sdk = has_min_sdk | sed('minSdkVersion| |=|\n', "") | head(1)
            device_min_sdk_version = self.device.get_min_sdk_version()
            if int(str(min_sdk)) > device_min_sdk_version:
                new_file = re.sub(r'minSdkVersion (.+)', r'minSdkVersion %d' % device_min_sdk_version,
                                  str(cat(gradle_file)))
                open(gradle_file, 'w').write(new_file)

    def needs_target_sdk_upgrade(self, gradle_file):
        has_target_sdk = cat(gradle_file) | grep(r'targetSdkVersion.*[0-9]+')
        if str(has_target_sdk) != "":
            device_target_sdk_version = self.device.get_device_sdk_version()
            new_file = re.sub(r'targetSdkVersion (.+)', r'targetSdkVersion %d' % device_target_sdk_version,
                              str(cat(gradle_file)))
            open(gradle_file, 'w').write(new_file)

    def __add_or_update_dexoptions(self, gradle_file):
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
        open(gradle_file, 'w').write(fl_ok)

    def __add_or_update_lintoptions(self, gradle_file):
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
        open(gradle_file, 'w').write(fl_ok)

    def __update_test_instrumentation_runner(self, gradle_file):
        file_ctent = str(cat(gradle_file))
        has_inst_runner = re.search(r'testInstrumentationRunner', file_ctent)
        if has_inst_runner is None:
            return
        device_sdk = self.device.get_device_sdk_version()
        # TODO it is advisable to compile with latest sdk
        adequate_test_runner = list(filter(lambda x: x[1] <= device_sdk, TEST_RUNNERS.items()))[-1]
        new_file = re.sub(r"testInstrumentationRunner (.+)",
                          r"testInstrumentationRunner '%s'" % adequate_test_runner[0], file_ctent)
        open(gradle_file, 'w').write(new_file)

    def __filter_opts(self, opts, excluding_set):
        to_keep = {}
        for dex_op in opts:
            opt_tpls = re.search(r'(.*?)(=|\s|:)([^{}]+)', dex_op.strip()).groups()
            opt_key = opt_tpls[0].strip()
            opt_oper = opt_tpls[1]
            opt_val = opt_tpls[2].strip()
            if opt_key not in excluding_set:
                to_keep[opt_key] = (opt_oper, opt_val)
            else:
                self.change_history.append("Removed or replaced opt %s" % opt_key)
        return to_keep

    def __add_or_replace_local_properties_files(self):
        local_props_files = mega_find(self.proj.proj_dir, pattern="local.properties", maxdepth=3)
        custom_prop_file_ctent = self.build_local_properties_file()
        for loc_prop in local_props_files:
            open(loc_prop, 'w').write(custom_prop_file_ctent)

    def build_local_properties_file(self):
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
            open(self.proj.root_build_file, 'w').write(new_file)

    def __add_external_libs_fldr(self, proj_module):
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
        bld_file = proj_module.build_file
        if not self.needs_external_lib_dependency():
            return
        file_ctent = str(cat(bld_file))
        dependencies = self.instrumenter.get_build_dependencies()
        has_depts = re.search(r'dependencies.*?\{', file_ctent)
        if has_depts is None:
            new_deps = "dependencies {"
            for n_dp in dependencies:
                new_deps += "\n\t" + gen_dependency_string(n_dp)
            new_deps += "\n}"
            new_file = file_ctent + "\n\n" + new_deps
            open(bld_file, 'w').write(new_file)
        else:
            # original_deps = re.search(r'dependencies.*?\{([^{}]+)}', file_ctent).groups()[0]  # .strip().split("\n")
            original_deps = re.search(r'dependencies.*?\{(.|\n)*}', file_ctent).group(0)
            original_deps_split = re.split(r'dependencies.*?\{', original_deps)
            original_deps = original_deps_split[1]
            original_deps = original_deps[0: len(original_deps) - 1]
            new_deps = ""
            for n_dp in dependencies:
                new_deps += gen_dependency_string(n_dp) + "\n\t"
            new_deps = original_deps + "\n\t" + new_deps + "\n"
            new_file = file_ctent.replace(original_deps, new_deps)
            open(bld_file, 'w').write(new_file)

    def needs_external_lib_dependency(self):
        return self.instrumenter.needs_build_dependency()

    def was_last_build_successful(self, task="build"):
        filename = self.proj.proj_dir + "/" + BUILD_RESULTS_FILE
        if os.path.exists(filename):
            with open(filename, 'r') as fl:
                js = json.load(fl)
            return js[task].lower() == SUCCESS_VALUE.lower() if task in js else False
        return False

    def regist_successfull_build(self, task="build"):
        filename = self.proj.proj_dir + "/" + BUILD_RESULTS_FILE
        js = {}
        if os.path.exists(filename):
            with open(filename, 'r') as fl:
                js = json.load(fl)

        js[task] = SUCCESS_VALUE
        with open(filename, 'w') as outfile:
            json.dump(js, outfile)

    def __set_build_tools_version(self, bld_file):
        has_bld_tools = str((cat(bld_file) | grep("buildToolsVersion") | sed("buildToolsVersion|\"", ""))).strip()
        if has_bld_tools != "":
            self.build_tools_version = DefaultSemanticVersion(has_bld_tools)

    def get_apk_version(apk):
        pass

    def __add_plugins(self, bld_file):
        if not self.instrumenter.needs_build_plugin():
            return
        file_content = str(cat(bld_file))
        plugins = self.instrumenter.get_build_plugins()
        has_plugin_apply = re.search(r'apply.*plugin.*', file_content)
        plg_string = ""
        if has_plugin_apply:
            # replace
            # plgs = echo(file_content) | grep(r'apply.*plugin')
            # it can't be the first plugin
            plgs = re.findall(r'apply.*plugin.*', file_content)
            for plg in plugins:
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
        open(bld_file, 'w').write(file_content)

    def __add_build_classpaths(self):
        if not self.instrumenter.needs_build_classpaths():
            return
        file_ctent = str(cat(self.proj.root_build_file))
        # TODO: more elegant way to do this, instead of just appending to build file
        classpaths = self.instrumenter.get_build_classpaths()

        pato_str = "buildscript{\n\tdependencies{\n"
        for pato in classpaths:
            pato_str += gen_dependency_string(pato) + "\n"
        new_file_ctnt = file_ctent + "\n" + pato_str + "\n}\n}"
        open(self.proj.root_build_file, 'w').write(new_file_ctnt)

    def __has_builded_apks(self):
        return len(mega_find(self.proj.proj_dir, pattern="*.apk", type_file='f')) > 0

    def needs_rebuild(self):
        return not self.__has_builded_apks()  # TODO check build type and maybe last build output, lint, etc
