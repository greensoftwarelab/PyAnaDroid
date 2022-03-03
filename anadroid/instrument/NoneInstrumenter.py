import os
from abc import ABC, abstractmethod
from shutil import copy

from anadroid.Types import BUILD_SYSTEM, TESTING_APPROACH, TESTING_FRAMEWORK
from anadroid.instrument.AbstractInstrumenter import AbstractInstrumenter
from anadroid.instrument.Types import INSTRUMENTATION_TYPE, INSTRUMENTATION_STRATEGY
from anadroid.utils.Utils import mega_find, logw

DEFAULT_LOG_FILENAME="instrumentation_log.json"

class NoneInstrumenter(AbstractInstrumenter):
    """Implements defined interface of AbstractInstrumenter to simulate instrumentation while not performing any
    project sources' changes.
   """
    def __init__(self, profiler, mirror_dirname="_TRANSFORMED_"):
        super().__init__(profiler, mirror_dirname)

    def init(self):
        pass

    def instrument(self, android_project, mirror_dirname="_TRANSFORMED_",test_approach=TESTING_APPROACH.WHITEBOX, test_frame=TESTING_FRAMEWORK.MONKEY,
                   instr_strategy=INSTRUMENTATION_STRATEGY.METHOD_CALL, instr_type=INSTRUMENTATION_TYPE.TEST, **kwargs):
        """
        just clone the project files to a new directory.
        """
        new_dir_name = f'NONE{mirror_dirname}'
        new_proj_dir = os.path.join(android_project.proj_dir, new_dir_name)
        if self.needs_reinstrumentation(android_project, test_approach, instr_type, instr_strategy):
            if not os.path.exists(new_proj_dir):
                os.mkdir(new_proj_dir)
            all_proj_files = list(map(lambda x: x.replace(android_project.proj_dir + "/", ""),
                                      filter(lambda t: mirror_dirname not in t, mega_find(android_project.proj_dir))))
            all_proj_files.sort(key=lambda s: len(s))
            for file_p in all_proj_files:
                full_file_path = os.path.join(android_project.proj_dir, file_p)
                target_file_path = os.path.join(android_project.proj_dir, new_dir_name, file_p)
                if os.path.exists(target_file_path):
                    continue
                elif os.path.isdir(full_file_path):
                    os.mkdir(target_file_path)
                elif not os.path.exists(target_file_path):
                    copy(full_file_path, target_file_path)
        else:
            logw("Same instrumentation of last time. Skipping instrumentation phase")
        return new_proj_dir

    def needs_build_plugin(self):
        return False

    def get_build_plugins(self):
        return {}

    def needs_build_dependency(self):
        return False

    def get_build_dependencies(self):
        return []


    def needs_build_classpaths(self):
        return False

    def get_build_classpaths(self):
       return []

    def get_log_filename(self):
        return DEFAULT_LOG_FILENAME
