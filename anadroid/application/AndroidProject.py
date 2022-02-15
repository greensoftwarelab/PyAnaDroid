import os
import re
import shutil
from enum import Enum
from os import mkdir, listdir

from textops import cat, grep, cut, sed, echo, grepv

from anadroid.application.Application import App
from anadroid.application.ProjectModule import ProjectModule
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import execute_shell_command, mega_find, get_results_dir, extract_version_from_apk

RESULTS_DIR = get_results_dir()

class BUILD_TYPE(Enum):
    RELEASE = "Release"
    DEBUG = "Debug"
    CUSTOM = "Custom"

class BUILD_FLAVOR(Enum):
    DEMO = "Demo"
    FULL = "full"
    CUSTOM = "Custom"
    NONE = "None" #just defaultconfig ?


def mk_ma_dir(path):
    try:
        mkdir(path)
    except FileExistsError:
        pass

def is_android_project(dirpath):
    return "settings.gradle" in [f for f in listdir(dirpath)]


class Project(object):
    def __init__(self, projname, projdir, results_dir=RESULTS_DIR):
        self.proj_name = projname
        self.proj_dir = projdir
        self.results_dir = results_dir

    def init_results_dir(self, app_id):
        res_app_dir = os.path.join(self.results_dir, app_id)
        mk_ma_dir(res_app_dir)
        self.results_dir = res_app_dir

    def clean_trasformations(self):
        transforms = mega_find(self.proj_dir, pattern="*TRANSFORMED*", maxdepth=1, type_file='d')
        for t in transforms:
            shutil.rmtree(t)

class AndroidProject(Project):
    def __init__(self, projname, projdir,results_dir=RESULTS_DIR):
        super(AndroidProject, self).__init__(projname=projname, projdir=projdir, results_dir=results_dir)
        self.root_build_file = self.get_root_build_file()
        self.main_manif_file = self.get_main_manif_file()
        self.tests_manif_file = None
        self.modules = {}
        self.__init_modules()
        self.pkg_name, self.app_id, = self.__gen_proj_id()
        super().init_results_dir(self.app_id)
        self.proj_version = DefaultSemanticVersion("0.0")
        self.apks = {'Test': [], 'Debug': [], 'Release': [], 'Custom': []}

    def __gen_proj_id(self):
        pkg_line = str(cat(self.main_manif_file) | grep("package=\"[^\"]"))
        pkg_name = str(re.search("package=(\"[^\"]*)", pkg_line).groups()[0]).strip().replace("\"", "")
        return pkg_name, self.proj_name + "--" + pkg_name

    def add_apk(self, apk_path, build_type):
        if build_type is None:
            tp = 'Test'
        else:
            tp = build_type.value

        self.apks[tp].append(apk_path)

    def get_build_files(self):
        return mega_find(self.proj_dir, maxdepth=3, mindepth=0, pattern="build.gradle", type_file='f')

    def get_root_build_file(self):
        out = sorted(mega_find(self.proj_dir, maxdepth=3, mindepth=1, pattern="build.gradle", type_file='f'), key=len)
        if len(out) > 0:
            return out[0]
        return None

    def get_main_manif_file(self):
        out = sorted(mega_find(self.proj_dir, maxdepth=5, mindepth=1, pattern="AndroidManifest.xml", type_file='f'), key=len)
        if len(out) > 0:
            return out[0]
        return None

    def get_gradle_settings(self):
        res = execute_shell_command("find %s -maxdepth 1 -type f -name \"settings.gradle\"" % self.proj_dir)
        res.validate()
        return res.output


    def __parse_modules(self, setts_file):
        modules = []
        modul_lines = cat(setts_file) | grep('include') | grepv(r"(^\s*//)") # | cut(sep=":", col=1) | sed(pats="\'|,", repls="")
        for mod_line in modul_lines:
            for mod in mod_line.split(","):
                module = str(echo(mod) | sed("include", "") | cut(sep=":", col=1) | sed(pats="\'|,", repls="")).strip()
                modules.append(module)
        return modules

    def __init_modules(self):
        setts_file = self.get_gradle_settings()
        modules = self.__parse_modules(setts_file)
        for mod_n in modules:
            mod_name = mod_n.strip()
            res = execute_shell_command("find %s -maxdepth 1 -type d -name \"%s\"" % (self.proj_dir, mod_name))
            if res.validate():
                self.modules[mod_name] = ProjectModule(mod_name, res.output.strip())
                #print(self.modules[mod_name].module_type)

    def get_gradle_plugin(self):
        gradle_plugin_version = str(cat(self.root_build_file) | grep("com.android.tools.build") | sed("classpath|com.android.tools.build:gradle:|\"", "")).strip()
        return gradle_plugin_version

    def create_inner_folder(self, name="libs"):
        path = os.path.join(self.proj_dir,name)
        try:
            mkdir(path)
        except FileExistsError:
            pass
        return path

    def has_gradle_wrapper(self):
        return len(mega_find(self.proj_dir, pattern="gradlew", maxdepth=2,type_file='f'))>0

    def get_apks(self, build_type=BUILD_TYPE.DEBUG):
        if len(self.apks[build_type.value]) > 0:
            return self.apks[build_type.value]
        vals = mega_find(self.proj_dir, pattern="*.apk", type_file='f')
        return list(filter(lambda x: build_type.value.lower() in x.lower(), vals))

    def get_test_apks(self):
        if len(self.apks['Test']) > 0:
            return self.apks['Test']
        vals = mega_find(self.proj_dir, pattern="*.apk", type_file='f')
        return list(filter(lambda x: 'test' in x.lower(), vals))

    def set_version(self, build_type):
        apks = self.get_apks(build_type)
        if len(apks) == 0:
            self.proj_version = DefaultSemanticVersion("0.0")
        ref_apk = apks[0] # assuming first since main apk is build before building tests apk
        v = extract_version_from_apk(ref_apk)
        self.proj_version = DefaultSemanticVersion(v)
