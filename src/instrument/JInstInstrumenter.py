from src.application.Dependency import BuildDependency, DependencyType
from src.instrument.AbstractInstrumenter import AbstractInstrumenter
import subprocess
from src.Types import BUILD_SYSTEM, TESTING_APPROACH, TESTING_FRAMEWORK
from src.instrument.Types import INSTRUMENTATION_TYPE, INSTRUMENTATION_STRATEGY
from src.utils.Utils import execute_shell_command

JINST_PATH = "/Users/ruirua/repos/pyAnaDroid/resources/jars/jInst.jar"  # loadFromConfig


class JInstInstrumenter(AbstractInstrumenter):
    def __init__(self, profiler, mirror_dirname="_TRANSFORMED_", build_system=BUILD_SYSTEM.GRADLE):
        self.build_system = build_system
        self.profiler = profiler
        self.mirror_dirname = type(profiler).__name__ + mirror_dirname
        self.build_dependencies=[]
        self.classpath_dependencies = {}
        self.build_plugins={}
        super().__init__()

    def init(self):
        pass

    def __update_dependencies_and_plugins(self, instr_type=INSTRUMENTATION_TYPE.TEST):
        self.build_dependencies=[]
        self.classpath_dependencies=[]
        self.build_plugins=[]
        if instr_type == INSTRUMENTATION_TYPE.ANNOTATION:
            self.build_dependencies.append(BuildDependency("com.quinn.hunter:hunter-debug-library", version="0.9.6"))
            self.classpath_dependencies.append(BuildDependency("com.quinn.hunter:hunter-debug-plugin",dep_type=DependencyType.CLASSPATH,  version="1.1.0"))
            self.classpath_dependencies.append(BuildDependency("com.quinn.hunter:hunter-transform", dep_type=DependencyType.CLASSPATH, version="1.1.0"))
            self.build_plugins.append("hunter-debug")


    def instrument(self, android_project, test_approach=TESTING_APPROACH.WHITEBOX, test_frame=TESTING_FRAMEWORK.MONKEY,
                   instr_strategy=INSTRUMENTATION_STRATEGY.METHOD_CALL, instr_type=INSTRUMENTATION_TYPE.TEST):
        self.__update_dependencies_and_plugins(instr_type)
        command = "java -jar \"{JInst_jar}\" -{build_system} \"{mir_dir}\" \"X\" \"{proj_dir}\" \"{manif_file}\" \"{test_manif_file}\" -{test_ori} -{test_frame} \"{app_id}\" -{test_approach}".format(
            JInst_jar=JINST_PATH,
            build_system=self.build_system.GRADLE.value.lower(),
            mir_dir=self.mirror_dirname,
            proj_dir=android_project.proj_dir,
            manif_file=android_project.main_manif_file,
            test_manif_file=android_project.tests_manif_file if android_project.tests_manif_file is not None else "-",
            test_ori=instr_type.value,
            test_frame=test_frame.value,
            app_id=android_project.app_id,
            test_approach=test_approach.value.lower()
        ) # # e.g java -jar jInst.jar "-gradle" "_TRANSFORMED_" "X" "./demoProjects/N2AppTest" "./demoProjects/N2AppTest/app/src/main/AndroidManifest.xml" "-" "-TestOriented" "-junit" "N2AppTest--uminho.di.greenlab.n2apptest" "blackbox"
        res = execute_shell_command(command)
        res.validate(Exception("Bad instrumentation"))
        return android_project.proj_dir + "/" + self.mirror_dirname

    def needs_build_plugin(self):
        return len(self.build_plugins) > 0

    def get_build_plugins(self):
        return self.build_plugins

    def needs_build_dependency(self):
        return len(self.get_build_dependencies()) >0

    def get_build_dependencies(self):
        val = list(self.build_dependencies)
        val.append(self.profiler.dependency)
        return val

    def needs_build_classpaths(self):
        return len(self.classpath_dependencies)>0

    def get_build_classpaths(self):
        return self.classpath_dependencies