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
    """Represents an Android Project Module.

    Attributes:
        mod_name (str): Module name.
        mod_dir (str): Module directory.
        build_file (str): Path to the build.gradle file of the module.
        module_type (MODULE_TYPE): Type of the module (LIBRARY or APP).
        manifest (str): Path to the AndroidManifest.xml file of the module.
        dependencies (set): Set of module dependencies.
        gen_apks (dict): Generated APKs within the module.
        gen_aars (dict): Generated AARs within the module.
    """
    def __init__(self, name, mod_dir):
        """Initializes a ProjectModule instance.

        Args:
            name (str): Module name.
            mod_dir (str): Module directory.
        """
        self.mod_name = name
        self.mod_dir = mod_dir
        self.build_file = self.__infer_build_file()
        self.module_type = self.__infer_module_type()
        self.manifest = self.__infer_manifest()
        self.dependencies = set()
        self.__infer_dependencies()
        self.gen_apks = {}
        self.gen_aars = {}

    def __infer_build_file(self):
        """Returns the path to the build.gradle file of the module.

        Returns:
            str: Filepath.
        """
        res = execute_shell_command("find \"%s\" -maxdepth 1 -type f -name \"build.gradle\"" % self.mod_dir)
        return res.output.strip() if res.return_code == 0 else None

    def __infer_manifest(self):
        """Returns the path to the AndroidManifest.xml file of the module.

        Returns:
            str: Filepath.
        """
        res = execute_shell_command("find \"%s\" -maxdepth 4 -type f -name \"AndroidManifest.xml\"" % self.mod_dir)
        return res.output.strip() if res.return_code == 0 else None

    def __infer_module_type(self):
        """Tries to infer the module type (MODULE_TYPE).

        Returns:
            MODULE_TYPE: Module type.
        """
        is_app = cat(self.build_file) | grep('com.android.application') != ''
        return MODULE_TYPE.APP if is_app else MODULE_TYPE.LIBRARY

    def __infer_dependencies(self):
        """Infers and adds module dependencies to the dependencies attribute."""
        # TODO: Get dependencies type
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
        """Creates a directory inside the module.

        Args:
            name (str): Directory name.

        Returns:
            str: Directory's path.
        """
        path = os.path.join(self.mod_dir, name)
        try:
            mkdir(path)
        except FileExistsError:
            pass
        return path
