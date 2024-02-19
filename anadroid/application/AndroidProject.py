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
    NONE = "None"


def mk_ma_dir(path):
    try:
        mkdir(path)
    except FileExistsError:
        pass


def is_android_project(dirpath):
    """Determines if a given directory is an Android Project.
    Looks for settings.gradle files.

    Args:
        dirpath (str): Path of the directory.

    Returns:
        bool: True if file is in the directory, False otherwise.
    """
    if not os.path.isdir(dirpath):
        return False
    return "settings.gradle" in [f for f in listdir(dirpath)]


class Project(object):
    """Class that abstracts software projects.

    Attributes:
        projname (str): Project name.
        projir (str): Project directory.
        results_dir (str): Directory where to store project's results.
    """
    def __init__(self, projname, projdir, results_dir=RESULTS_DIR):
        """Initializes a Project instance.

        Args:
            projname (str): Project name.
            projdir (str): Project directory.
            results_dir (str): Directory where to store project's results.
        """
        self.proj_name = projname
        self.proj_dir = projdir
        self.results_dir = results_dir
        self.apps = []

    def init_results_dir(self, app_id):
        """Initializes results directory.
        Creates directory if it does not exist.

        Args:
            app_id (str): Project's app id.
        """
        res_app_dir = os.path.join(self.results_dir, app_id)
        mk_ma_dir(res_app_dir)
        self.results_dir = res_app_dir

    def clean_transformations(self):
        """Removes previous project transformations from project sources."""
        transforms = mega_find(self.proj_dir, pattern="*TRANSFORMED*", maxdepth=1, type_file='d')
        for t in transforms:
            shutil.rmtree(t)

    def save_proj_json(self, path):
        """Saves project details to a JSON file.

        Args:
            path (str): Path where the JSON file will be saved.
        """
        pass


class AndroidProject(Project):
    """Class that abstracts Android Projects.

    Attributes:
        projname (str): Project name.
        projir (str): Project directory.
        results_dir (str): Directory where to store project's results.
        root_build_file (str): Project-level gradle file.
        main_manif_file (str): Project manifest file.
        tests_manif_file: Manifest of the test project.
    """
    def __init__(self, projname, projdir, results_dir=RESULTS_DIR, clean_instrumentations=False):
        """Initializes an AndroidProject instance.

        Args:
            projname (str): Project name.
            projdir (str): Project directory.
            results_dir (str): Directory where to store project's results.
            clean_instrumentations (bool): Clean instrumentations flag.
        """
        super(AndroidProject, self).__init__(projname=projname, projdir=projdir, results_dir=results_dir)
        self.root_build_file = self.get_root_build_file()
        self.main_manif_file = self.get_main_manif_file()
        self.tests_manif_file = None
        self.modules = {}
        self.__init_modules()
        self.pkg_name, self.app_id = self.__gen_proj_id()
        super().init_results_dir(self.app_id)
        self.proj_version = DefaultSemanticVersion("0.0")
        self.apks = {'Test': [], 'Debug': [], 'Release': [], 'Custom': []}
        if clean_instrumentations:
            self.clean_transformations()

    def __gen_proj_id(self):
        """Generates project's UID.

        Returns:
            Tuple[str, str]: Package name and project ID.
        """
        pkg_line = str(cat(self.main_manif_file) | grep("package=\"[^\"]"))
        pkg_name = str(re.search("package=(\"[^\"]*)", pkg_line).groups()[0]).strip().replace("\"", "")
        return pkg_name, self.proj_name + "--" + pkg_name

    def add_apk(self, apk_path, build_type):
        """Adds an APK path of the specified build type to the known list of APKs for the project.

        Args:
            apk_path (str): Path to APK.
            build_type (BUILD_TYPE): APK build type (test, release, custom).
        """
        if build_type is None:
            tp = 'Test'
        else:
            tp = build_type.value

        self.apks[tp].append(apk_path)

    def get_build_files(self):
        """Returns build.gradle files of the project.

        Returns:
            files_list (:obj:`list` of :obj:`str`): List of file paths.
        """
        return mega_find(self.proj_dir, maxdepth=3, mindepth=0, pattern="build.gradle", type_file='f')

    def get_root_build_file(self):
        """Returns project-level build.gradle file.

        Assumes that it is the one with the shortest path.
        Gets the list of the build.gradle file paths and returns the shortest one.

        Returns:
            file_path (str): Path of gradle file.
        """
        out = sorted(mega_find(self.proj_dir, maxdepth=3, mindepth=1, pattern="build.gradle", type_file='f'), key=len)
        if len(out) > 0:
            return out[0]
        return None

    def get_main_manif_file(self):
        """Returns project's main manifest file.

        Returns:
            file_path (str): Path of the main manifest file.
        """
        out = sorted(mega_find(self.proj_dir, maxdepth=5, mindepth=1, pattern="AndroidManifest.xml", type_file='f'), key=len)
        if len(out) > 0:
            return out[0] if "test" not in str(out[0]).lower() else out[-1]
        return None

    def get_gradle_settings(self):
        """Returns settings.gradle file.

        Returns:
            file_path (str): Path of the settings.gradle file.
        """
        res = execute_shell_command("find %s -maxdepth 1 -type f -name \"settings.gradle\"" % self.proj_dir)
        res.validate()
        return res.output

    def __parse_modules(self, setts_file):
        """Parses project modules.

        Args:
            setts_file: settings.gradle file containing references to the modules.

        Returns:
            modules (:obj:`list` of :obj:`str`): List of module names.
        """
        modules = []
        modul_lines = cat(setts_file) | grep('include') | grepv(r"(^\s*//)")  # | cut(sep=":", col=1) | sed(pats="\'|,", repls="")
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
        """Initialize project modules.
        For each module contained in settings.gradle file, constructs a ProjectModule object and adds it to the modules dict.
        """
        setts_file = self.get_gradle_settings()
        modules = self.__parse_modules(setts_file)
        for mod_n in modules:
            mod_name = mod_n.strip()
            res = execute_shell_command("find %s -maxdepth 1 -type d -name \"%s\"" % (self.proj_dir, mod_name))
            if res.validate() and res.output.strip() != "":
                self.modules[mod_name] = ProjectModule(mod_name, res.output.strip())

    def get_gradle_plugin(self):
        """Returns the gradle plugin version.

        Parses gradle plugin version from the root build file.

        Returns:
            gradle_plugin_version (str): Gradle plugin version.
        """
        gradle_plugin_version = str(cat(self.root_build_file) | grep("com.android.tools.build") | sed("classpath|com.android.tools.build:gradle:|\"", "")).strip().replace("'", "")
        return gradle_plugin_version

    def create_inner_folder(self, name="libs"):
        """Creates a folder inside the project.

        Args:
            name (str): Name of the folder to be created.

        Returns:
            path (str): Path of the created folder.
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
            bool: True if gradlew file is found in project's sources, False otherwise.
        """
        return len(mega_find(self.proj_dir, pattern="gradlew", maxdepth=2, type_file='f')) > 0

    def get_apks(self, build_type=BUILD_TYPE.DEBUG):
        """Get APKs of a specific build type.

        Args:
            build_type (BUILD_TYPE): Build type.

        Returns:
            apk_list (:obj:`list` of :obj:`str`): List of APK paths.
        """
        if len(self.apks[build_type.value]) > 0:
            return self.apks[build_type.value]
        vals = mega_find(self.proj_dir, pattern="*.apk", type_file='f')
        return list(filter(lambda x: build_type.value.lower() in x.lower(), vals))

    def get_test_apks(self):
        """Returns test APKs.

        Returns:
            apk_list (:obj:`list` of :obj:`str`): List of test APK paths.
        """
        if len(self.apks['Test']) > 0:
            return self.apks['Test']
        vals = mega_find(self.proj_dir, pattern="*.apk", type_file='f')
        return list(filter(lambda x: 'test' in x.lower(), vals))

    def set_version(self, build_type):
        """Set the project version based on the specified build type.

        Args:
            build_type (BUILD_TYPE): Build type.
        """
        apks = self.get_apks(build_type)
        if len(apks) == 0:
            self.proj_version = DefaultSemanticVersion("0.0")
        ref_apk = apks[0]  # Assuming first since the main APK is built before building test APKs
        v = extract_version_from_apk(ref_apk)
        self.proj_version = DefaultSemanticVersion(v)

    def get_proj_json(self):
        """Get a dictionary containing project information.

        Returns:
            dict: A dictionary containing project details.
        """
        return {
            'project_id': self.proj_name,
            'project_desc': '',
            'project_build_tool': "gradle",
            'project_packages': [self.pkg_name],
            'project_location': self.proj_dir,
            'project_apps': [x.get_app_json() for x in self.apps]
        }

    def save_proj_json(self, path):
        """Save the project information to a JSON file.

        Args:
            path (str): Path where the JSON file will be saved.
        """
        js = self.get_proj_json()
        filename = f'{self.app_id}.json'
        with open(os.path.join(path, filename), 'w') as jj:
            json.dump(js, jj)
