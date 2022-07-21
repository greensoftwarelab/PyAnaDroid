import json
import os
import re
import shutil
from enum import Enum
from os import mkdir, listdir

from textops import cat, grep, cut, sed, echo, grepv
from anadroid.application.ProjectModule import ProjectModule
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.utils.Utils import execute_shell_command, mega_find, get_results_dir, extract_version_from_apk, logw

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
    """determines if a given directory is an Android Project.
    looks for settings.gradle files.
    Args:
        dirpath: path of the directory.

    Returns:
        bool: True if file is in diretory, False otherwise.
    """
    return "settings.gradle" in [f for f in listdir(dirpath)]


class Project(object):
    """Class that abstracts Projects.

   Attributes:
       projname: project name.
       projir: project directory.
       results_dir: directory where to store project' results.
   """
    def __init__(self, projname, projdir, results_dir=RESULTS_DIR):
        self.proj_name = projname
        self.proj_dir = projdir
        self.results_dir = results_dir
        self.apps = []

    def init_results_dir(self, app_id):
        """inits results dir.
        Create directory if not exists.
        Args:
            app_id: project's app id.
        """
        res_app_dir = os.path.join(self.results_dir, app_id)
        mk_ma_dir(res_app_dir)
        self.results_dir = res_app_dir

    def clean_trasformations(self):
        """remove previous project' transformations from project sources."""
        transforms = mega_find(self.proj_dir, pattern="*TRANSFORMED*", maxdepth=1, type_file='d')
        for t in transforms:
            shutil.rmtree(t)

    def save_proj_json(self, path):
        pass


class AndroidProject(Project):
    """Class that abstracts Android Projects.

       Attributes:
           projname: project name.
           projir: project directory.
           results_dir: directory where to store project' results.
           root_build_file = project level gradle file.
           main_manif_file = project manifest file.
           tests_manif_file = manifest of test project.
       """
    def __init__(self, projname, projdir, results_dir=RESULTS_DIR, clean_instrumentations=False):
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
        if clean_instrumentations:
            self.clean_trasformations()

    def __gen_proj_id(self):
        """generates project's uid.
        Returns:

        """
        pkg_line = str(cat(self.main_manif_file) | grep("package=\"[^\"]"))
        pkg_name = str(re.search("package=(\"[^\"]*)", pkg_line).groups()[0]).strip().replace("\"", "")
        return pkg_name, self.proj_name + "--" + pkg_name

    def add_apk(self, apk_path, build_type):
        """adds apk path of build_type to the known list of apks of the project.
        Args:
            apk_path: path to apk.
            build_type: apk build type (test, release, custom).
        """
        if build_type is None:
            tp = 'Test'
        else:
            tp = build_type.value

        self.apks[tp].append(apk_path)

    def get_build_files(self):
        """returns build.gradle files of the project.
        Returns:
            files_list(:obj:`list` of :obj:`str`): list of files.
        """
        return mega_find(self.proj_dir, maxdepth=3, mindepth=0, pattern="build.gradle", type_file='f')

    def get_root_build_file(self):
        """Returns project level build.gradle file.
        Assumes that it the one with the shortest path. Gets the list of the build.gradle file paths
        and returns the shortest one.

        Returns:
            file_path(str): path of gradle file.
        """
        out = sorted(mega_find(self.proj_dir, maxdepth=3, mindepth=1, pattern="build.gradle", type_file='f'), key=len)
        if len(out) > 0:
            return out[0]
        return None

    def get_main_manif_file(self):
        """Returns project's manifest file.

        Returns:
            file_path(str): path of manifest file.
        """
        out = sorted(mega_find(self.proj_dir, maxdepth=5, mindepth=1, pattern="AndroidManifest.xml", type_file='f'), key=len)
        if len(out) > 0:
            return out[0] if "test" not in str(out[0]).lower() else out[-1]
        return None

    def get_gradle_settings(self):
        """Returns settings.gradle file

        Returns:
            file_path(str): path of  file.
        """
        res = execute_shell_command("find %s -maxdepth 1 -type f -name \"settings.gradle\"" % self.proj_dir)
        res.validate()
        return res.output

    def __parse_modules(self, setts_file):
        """Parses project modules.
        Args:
            setts_file: settings.gradle file containing referring the modules.
        Returns:
            modules(:obj:`list` of :obj:`str`): list of modules.
        """
        modules = []
        modul_lines = cat(setts_file) | grep('include') | grepv(r"(^\s*//)") # | cut(sep=":", col=1) | sed(pats="\'|,", repls="")
        for mod_line in modul_lines:
            for mod in mod_line.split(","):
                module_name = str(echo(mod) | sed("include", "") | cut(sep=":", col=1) | sed(pats="\'|,", repls="")).strip()
                module_is_not_empty = any(mega_find(os.path.join(self.proj_dir, module_name), maxdepth=2, mindepth=1))
                if module_is_not_empty:
                    modules.append(module_name)
                else:
                    logw(f"ignoring empty module {module_name}")
        return modules

    def __init_modules(self):
        """Init project modules.
        For each module contained in settings.gradle file, constructs a ProjectModule obj and adds it the modules dict.
        """
        setts_file = self.get_gradle_settings()
        modules = self.__parse_modules(setts_file)
        for mod_n in modules:
            mod_name = mod_n.strip()
            res = execute_shell_command("find %s -maxdepth 1 -type d -name \"%s\"" % (self.proj_dir, mod_name))
            if res.validate() and res.output.strip() != "":
                self.modules[mod_name] = ProjectModule(mod_name, res.output.strip())
                #print(self.modules[mod_name].module_type)

    def get_gradle_plugin(self):
        """Returns gradle plugin version.

        Parses gradle plugin version from root build file.
        Returns:
            gradle_plugin_version(str): plugin version.
        """
        gradle_plugin_version = str(cat(self.root_build_file) | grep("com.android.tools.build") | sed("classpath|com.android.tools.build:gradle:|\"", "")).strip().replace("'","")
        return gradle_plugin_version

    def create_inner_folder(self, name="libs"):
        """creates folder inside project.
        Args:
            name: name of the folder to be created.

        Returns:
            path(str): path of the created folder.
        """
        path = os.path.join(self.proj_dir, name)
        try:
            mkdir(path)
        except FileExistsError:
            pass
        return path

    def has_gradle_wrapper(self):
        """Determine if the project is ready to be built with gradle wrapper.
        Returns:
            bool: True if gradlew file in project' sources, False otherwise.
        """
        return len(mega_find(self.proj_dir, pattern="gradlew", maxdepth=2, type_file='f')) > 0

    def get_apks(self, build_type=BUILD_TYPE.DEBUG):
        """get apks of a build type.
        Args:
            build_type: build type.

        Returns:
            apk_list(:obj:`list` of :obj:`str`): list of apk paths.
        """
        if len(self.apks[build_type.value]) > 0:
            return self.apks[build_type.value]
        vals = mega_find(self.proj_dir, pattern="*.apk", type_file='f')
        return list(filter(lambda x: build_type.value.lower() in x.lower(), vals))

    def get_test_apks(self):
        """returns test apks.
        Returns:
            apk_list(:obj:`list` of :obj:`str`): list of test apks' paths.
        """
        if len(self.apks['Test']) > 0:
            return self.apks['Test']
        vals = mega_find(self.proj_dir, pattern="*.apk", type_file='f')
        return list(filter(lambda x: 'test' in x.lower(), vals))

    def set_version(self, build_type):
        """set project version.
        Returns:
            object:
        """
        apks = self.get_apks(build_type)
        if len(apks) == 0:
            self.proj_version = DefaultSemanticVersion("0.0")
        ref_apk = apks[0] # assuming first since main apk is build before building tests apk
        v = extract_version_from_apk(ref_apk)
        self.proj_version = DefaultSemanticVersion(v)

    def get_proj_json(self):
        return {
            'project_id': self.proj_name,
            'project_desc': '',
            'project_build_tool': "gradle",
            'project_packages': [self.pkg_name],
            'project_location': self.proj_dir,
            'project_apps': [ x.get_app_json() for x in self.apps ]
        }

    def save_proj_json(self, path):
        js = self.get_proj_json()
        filename = f'{self.app_id}.json'
        with open(os.path.join(path, filename), 'w') as jj:
            json.dump(js, jj)
