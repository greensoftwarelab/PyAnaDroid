import json,os
import shutil

from src.application.Dependency import BuildDependency, DependencyType
from src.instrument.AbstractInstrumenter import AbstractInstrumenter
import subprocess
from src.Types import BUILD_SYSTEM, TESTING_APPROACH, TESTING_FRAMEWORK
from src.instrument.Types import INSTRUMENTATION_TYPE, INSTRUMENTATION_STRATEGY
from src.utils.Utils import execute_shell_command

JINST_PATH = "resources/jars/jInst.jar"  # loadFromConfig



class JInstInstrumenter(AbstractInstrumenter):
    def __init__(self, profiler, mirror_dirname="_TRANSFORMED_", build_system=BUILD_SYSTEM.GRADLE):
        self.build_system = build_system
        self.profiler = profiler
        self.mirror_dirname = type(profiler).__name__ + mirror_dirname
        self.build_dependencies=[]
        self.classpath_dependencies = {}
        self.build_plugins={}
        super().__init__()

    def get_log_filename(self):
        return super().get_log_filename()

    def init(self):
        pass

    def __update_dependencies_and_plugins(self,):
        self.build_dependencies.clear()
        self.classpath_dependencies.clear()
        self.build_plugins.clear()
        if self.current_instr_type == INSTRUMENTATION_TYPE.ANNOTATION:
            self.build_dependencies.append(BuildDependency("io.github.raphael28:hunter-debug-library", version="0.9.8"))
            #self.classpath_dependencies.append(BuildDependency("io.github.raphael28:hunter-debug-plugin",dep_type=DependencyType.CLASSPATH,  version="0.9.8"))
            #self.classpath_dependencies.append(BuildDependency("io.github.raphael28:hunter-transform", dep_type=DependencyType.CLASSPATH, version="0.9.5"))
            #self.build_plugins.append("hunter-debug")


    def instrument(self, android_project, test_approach=TESTING_APPROACH.WHITEBOX, test_frame=TESTING_FRAMEWORK.MONKEY,
                   instr_strategy=INSTRUMENTATION_STRATEGY.METHOD_CALL, instr_type=INSTRUMENTATION_TYPE.TEST):
        self.current_instr_type = instr_type
        self.__update_dependencies_and_plugins()
        if self.needs_reinstrumentation(android_project,test_approach, instr_type, instr_strategy):
            print("instrumenting")
            command = "java -jar \"{JInst_jar}\" -{build_system} \"{mir_dir}\" \"X\" \"{proj_dir}\" \"{manif_file}\" \"{test_manif_file}\" -{test_ori} -{test_frame} \"{app_id}\" -{test_approach}".format(
                JInst_jar=JINST_PATH,
                build_system=self.build_system.GRADLE.value.lower(),
                mir_dir=self.mirror_dirname,
                proj_dir=android_project.proj_dir,
                manif_file=android_project.main_manif_file,
                test_manif_file=android_project.tests_manif_file if android_project.tests_manif_file is not None else "-",
                test_ori=self.current_instr_type.value,
                test_frame=test_frame.value,
                app_id=android_project.app_id,
                test_approach=test_approach.value.lower()
            ) # # e.g java -jar jInst.jar "-gradle" "_TRANSFORMED_" "X" "./demoProjects/N2AppTest" "./demoProjects/N2AppTest/app/src/main/AndroidManifest.xml" "-" "-TestOriented" "-junit" "N2AppTest--uminho.di.greenlab.n2apptest" "blackbox"
            res = execute_shell_command(command)
            res.validate(Exception("Bad instrumentation"))
            self.write_instrumentation_log_file(android_project,test_approach, instr_type, instr_strategy)
            all_m_file = "allMethods.json"
            if os.path.exists(all_m_file):
                shutil.copy(all_m_file, os.path.join(android_project.proj_dir, all_m_file) )
        else:
            print("Same instrumentation of last time. Skipping instrumentation phase")

        return android_project.proj_dir + "/" + self.mirror_dirname

    def needs_build_plugin(self):
        return len(self.build_plugins) > 0

    def get_build_plugins(self):
        return self.build_plugins

    def needs_build_dependency(self):
        return len(self.get_build_dependencies()) >0

    def get_build_dependencies(self):
        val = list(self.build_dependencies)
        if self.profiler.dependency != None:
            val.append(self.profiler.dependency)
        return val

    def needs_build_classpaths(self):
        return len(self.classpath_dependencies)>0

    def get_build_classpaths(self):
        return self.classpath_dependencies

    def needs_reinstrumentation(self,proj,test_approach, instr_type, instr_strategy):
        instrumentation_log = self.__getInstrumentationLog(proj)
        old_profiler = instrumentation_log['profiler'] if 'profiler' in instrumentation_log else ""
        old_approach = instrumentation_log['test_approach'] if 'test_approach' in instrumentation_log else ""
        old_instr_type = instrumentation_log['instr_type'] if 'instr_type' in instrumentation_log else ""
        old_instr_strat = instrumentation_log['instr_strategy'] if 'instr_strategy' in instrumentation_log else ""
        return self.profiler.__class__.__name__ != old_profiler \
               or old_approach != test_approach.value \
                    or old_instr_type != instr_type.value \
                        or old_instr_strat != instr_strategy.value

    def write_instrumentation_log_file(self,proj,test_approach, instr_type, instr_strategy):
        data = {
            'profiler': self.profiler.__class__.__name__,
            'test_approach': test_approach.value,
            'instr_type': instr_type.value,
            'instr_strategy': instr_strategy.value
        }
        filepath = proj.proj_dir + "/" + self.mirror_dirname + "/" + self.get_log_filename()
        with open( filepath, 'w') as outfile:
            json.dump(data, outfile)



    def __getInstrumentationLog(self,proj):
        file = self.get_log_filename()
        filepath = proj.proj_dir + "/" + self.mirror_dirname + "/" +file
        js={}
        if os.path.exists(filepath):
            with open(filepath, "r") as ff:
                js = json.load(ff)
        return js
