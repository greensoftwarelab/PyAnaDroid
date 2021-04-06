from enum import Enum
from os import mkdir

from src.utils.Utils import execute_shell_command
from textops import cat, grep, cut
import re
class MODULE_TYPE(Enum):
    LIBRARY = "Library"
    APP = "App"



class ProjectModule(object):
    def __init__(self, name, mod_dir):
        self.mod_name = name
        self.mod_dir = mod_dir
        self.build_file = self.__infer_build_file()
        self.module_type = self.__infer_module_type()
        self.manifest = self.__infer_manifest()
        self.dependencies = set()
        self.__infer_dependencies()
        #self.main_dir = None
        #self.inst_test_dir = None
        #self.test_dir = None
        #self.beuild_dir = None
        #self.libs_dir = None
        self.gen_apks = {}
        self.gen_aars = {}


    def __infer_build_file(self):
        res = execute_shell_command("find \"%s\" -maxdepth 1 -type f -name \"build.gradle\"" % self.mod_dir)
        return res.output.strip() if res.return_code == 0 else None

    def __infer_manifest(self):
        res = execute_shell_command("find \"%s\" -maxdepth 4 -type f -name \"AndroidManifest.xml\"" % self.mod_dir)
        return res.output.strip() if res.return_code == 0 else None

    def __infer_module_type(self):
        is_app = cat(self.build_file) | grep('com.android.application') != ''
        return MODULE_TYPE.APP if is_app else MODULE_TYPE.LIBRARY

    def __infer_dependencies(self):
        # TODO get dependencies type
        inside_dependencies = re.search(r'dependencies.*?\{([^{}]+)}', str(cat(self.build_file))).groups(0)[0]
        for dep_line in inside_dependencies.splitlines():
            is_imp = str(grep(dep_line, pattern="implementation"))
            if is_imp != "":
                dependency, name, vers = re.search('(\'|\")(.*?)(\'|\")', is_imp)[2] | cut(sep=":")
            else:
                is_comp = str(grep(dep_line, pattern="compile"))
                if is_comp != "":
                    dependency = re.search('name:(.*?)(\'|\")(.*?)(\'|\"),', is_comp).groups()[2]
        self.dependencies.add(dependency)

    def create_inner_folder(self, name="libs"):
        path = self.mod_dir + "/" + name
        try:
            mkdir(path)
        except FileExistsError:
            pass
        return path