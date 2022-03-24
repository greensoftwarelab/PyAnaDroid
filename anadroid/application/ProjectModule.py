import os
from enum import Enum
from os import mkdir

from anadroid.utils.Utils import execute_shell_command, loge
from textops import cat, grep, cut
import re


class MODULE_TYPE(Enum):
    """Project Module types."""
    LIBRARY = "Library"
    APP = "App"


class ProjectModule(object):
    """Represents an Android Project Module (https://developer.android.com/studio/projects#ApplicationModules).
        Attributes:
            name(str): module name.
            mod_dir(str): module directory.
        """
    def __init__(self, name, mod_dir):
        self.mod_name = name
        self.mod_dir = mod_dir
        self.build_file = self.__infer_build_file()
        self.module_type = self.__infer_module_type()
        self.manifest = self.__infer_manifest()
        self.dependencies = set()
        self.__infer_dependencies()
        # self.main_dir = None
        # self.inst_test_dir = None
        # self.test_dir = None
        # self.beuild_dir = None
        # self.libs_dir = None
        self.gen_apks = {}
        self.gen_aars = {}

    def __infer_build_file(self):
        """returns build.gradle filepath of module.
        Returns:
            mod(str): filepath.
        """
        res = execute_shell_command("find \"%s\" -maxdepth 1 -type f -name \"build.gradle\"" % self.mod_dir)
        return res.output.strip() if res.return_code == 0 else None

    def __infer_manifest(self):
        """Returns module's manifest file.
        Looks for AndroidManifest.xml files in mod_dir.
        Returns:
             filepath(str): filepath.
        """
        res = execute_shell_command("find \"%s\" -maxdepth 4 -type f -name \"AndroidManifest.xml\"" % self.mod_dir)
        return res.output.strip() if res.return_code == 0 else None

    def __infer_module_type(self):
        """Tries to infer the module type (`MODULE_TYPE`).
        Returns:
            mod_type(:obj:`MODULE_TYPE`): module type.
        """
        is_app = cat(self.build_file) | grep('com.android.application') != ''
        return MODULE_TYPE.APP if is_app else MODULE_TYPE.LIBRARY

    def __infer_dependencies(self):
        """Infers and add module dependencies to dependencies attribute."""
        # TODO get dependencies type
        dependencies = re.search(r'dependencies.*?\{(.|\n)*}', str(cat(self.build_file)))
        inside_dependencies = []
        if dependencies:
            dependencies = dependencies.group(0)
            inside_dependencies = dependencies.splitlines()
        dependency = ""
        for dep_line in inside_dependencies:
            is_imp = str(grep(dep_line, pattern="implementation"))
            if is_imp != "":
                splits = re.search('(\'|\")(.*)(\'|\"?)', is_imp)
                if splits is not None:
                    dependency = splits.groups()[1].split(":")[0]
                else:
                    loge(f"error detecting dependencies of module {self.mod_name}")
            else:
                is_comp = str(grep(dep_line, pattern="compile"))
                if is_comp != "":
                    dependency = re.search('name:(.*?)(\'|\")(.*?)(\'|\"),', is_comp)
                    if dependency:
                        dependency = dependency.groups()[1]
        self.dependencies.add(dependency)

    def create_inner_folder(self, name="libs"):
        """creates directory  inside module.
        Args:
            name: directory name.
        Returns:
            path(str): directory's path.
        """
        path = os.path.join(self.mod_dir, name)
        try:
            mkdir(path)
        except FileExistsError:
            pass
        return path
