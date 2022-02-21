import json
import os
from abc import ABC, abstractmethod

from anadroid.Types import TESTING_APPROACH, TESTING_FRAMEWORK
from anadroid.instrument.Types import INSTRUMENTATION_STRATEGY, INSTRUMENTATION_TYPE

DEFAULT_LOG_FILENAME = "instrumentation_log.json"

class AbstractInstrumenter(ABC):
    def __init__(self, profiler, mirror_dirname="_TRANSFORMED_"):
        super().__init__()
        self.profiler = profiler
        self.current_instr_type = None
        self.mirror_dirname = type(profiler).__name__ + mirror_dirname

    @abstractmethod
    def init(self):
        pass

    @abstractmethod
    def instrument(self, android_project, mirror_dirname="_TRANSFORMED_", test_approach=TESTING_APPROACH.WHITEBOX, test_frame=TESTING_FRAMEWORK.MONKEY,
                   instr_strategy=INSTRUMENTATION_STRATEGY.METHOD_CALL, instr_type=INSTRUMENTATION_TYPE.TEST, **kwargs):
        pass

    @abstractmethod
    def needs_build_plugin(self):
        pass

    @abstractmethod
    def get_build_plugins(self):
       pass

    @abstractmethod
    def needs_build_dependency(self):
        pass

    @abstractmethod
    def get_build_dependencies(self):
        pass

    @abstractmethod
    def needs_build_classpaths(self):
        pass

    @abstractmethod
    def get_build_classpaths(self):
       pass

    @abstractmethod
    def get_log_filename(self):
        return DEFAULT_LOG_FILENAME

    def needs_reinstrumentation(self, proj, test_approach, instr_type, instr_strategy):
        instrumentation_log = self.get_instrumentation_log(proj)
        old_profiler = instrumentation_log['profiler'] if 'profiler' in instrumentation_log else ""
        old_approach = instrumentation_log['test_approach'] if 'test_approach' in instrumentation_log else ""
        old_instr_type = instrumentation_log['instr_type'] if 'instr_type' in instrumentation_log else ""
        old_instr_strat = instrumentation_log['instr_strategy'] if 'instr_strategy' in instrumentation_log else ""
        return self.profiler.__class__.__name__ != old_profiler \
               or old_approach != test_approach.value \
               or old_instr_type != instr_type.value \
               or old_instr_strat != instr_strategy.value

    def write_instrumentation_log_file(self, proj, test_approach, instr_type, instr_strategy):
        data = {
            'profiler': self.profiler.__class__.__name__,
            'test_approach': test_approach.value,
            'instr_type': instr_type.value,
            'instr_strategy': instr_strategy.value
        }
        filepath = os.path.join(proj.proj_dir, self.mirror_dirname, self.get_log_filename())
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile)

    def get_instrumentation_log(self, proj):
        file = self.get_log_filename()
        filepath = os.path.join(proj.proj_dir, self.mirror_dirname, file)
        js = {}
        if os.path.exists(filepath):
            with open(filepath, "r") as ff:
                js = json.load(ff)
        return js