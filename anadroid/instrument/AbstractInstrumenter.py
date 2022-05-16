import json
import os
from abc import ABC, abstractmethod

from anadroid.Types import TESTING_APPROACH, TESTING_FRAMEWORK
from anadroid.instrument.Types import INSTRUMENTATION_STRATEGY, INSTRUMENTATION_TYPE

DEFAULT_LOG_FILENAME = "instrumentation_log.json"


class AbstractInstrumenter(ABC):
    """Provides basic interface to perform instrumentation of project sources of Android projects.
    Attributes:
        profiler(Profiler): targeted profiler.
        mirror_dirname(str): name of the directory where the changes will be performed.
    """
    def __init__(self, profiler, mirror_dirname="_TRANSFORMED_"):
        super().__init__()
        self.profiler = profiler
        self.current_instr_type = None
        self.mirror_dirname = type(profiler).__name__ + mirror_dirname

    @abstractmethod
    def init(self):
        """inits class."""
        pass

    @abstractmethod
    def instrument(self, android_project, mirror_dirname="_TRANSFORMED_", test_approach=TESTING_APPROACH.WHITEBOX, test_frame=TESTING_FRAMEWORK.MONKEY,
                   instr_strategy=INSTRUMENTATION_STRATEGY.METHOD_CALL, instr_type=INSTRUMENTATION_TYPE.TEST, **kwargs):
        """Method responsible for instrument project sources.
        Args:
            android_project(AndroidProject): the project to instrument.
            mirror_dirname(str): name of the directory where the changes will be performed.
            test_approach(TESTING_APPROACH): testing approach.
            test_frame(TESTING_FRAMEWORK): the testing framework to be used.
            instr_strategy(INSTRUMENTATION_STRATEGY): instrumentation strategy to perform.
            instr_type(INSTRUMENTATION_TYPE): type of instrumentation.
            **kwargs:
        """
        pass

    @abstractmethod
    def needs_build_plugin(self):
        """checks if a build plugin is needed."""
        pass

    @abstractmethod
    def get_build_plugins(self):
        """retrieves the needed build plugins for the performed instrumentation."""
        pass

    @abstractmethod
    def needs_build_dependency(self):
        """checks if additional build dependencies are needed."""
        pass

    @abstractmethod
    def get_build_dependencies(self):
        """retrieves the needed build dependencies for the performed instrumentation."""
        pass

    @abstractmethod
    def needs_build_classpaths(self):
        """checks if additional gradle dependencies are needed for the performed instrumentation."""
        pass

    @abstractmethod
    def get_build_classpaths(self):
        """retrieves the needed gradle dependencies for the performed instrumentation."""
        pass

    @abstractmethod
    def get_log_filename(self):
        """returns the name of the log file where the instrumentation output will be written.
        Returns:
            str: name of the file.
        """
        return DEFAULT_LOG_FILENAME

    def needs_reinstrumentation(self, proj, test_approach, instr_type, instr_strategy):
        """checks if the project needs to be instrumented again (i.e. if the last instrumentation performed
        is == to the instrumentation to be performed).
        Args:
            proj(AndroidProject): project.
            test_approach(TESTING_APPROACH): testing approach.
            instr_strategy(INSTRUMENTATION_STRATEGY): instrumentation strategy to perform.
            instr_type(INSTRUMENTATION_TYPE): type of instrumentation.

        Returns:
            bool: True if needs to be instrumented again, False otherwise.
        """
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
        """write instrumentation attributes to  a file.
        This file is inspected when there is need to evaluate if there is need to instrument again.
        Args:
            proj:
            test_approach:
            instr_type:
            instr_strategy:
        """
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
        """loads information from the file containing the specs of the last instrumentation performed.
        Args:
            proj(AndroidProject): project.

        Returns:
            dict: last instrumentation specs.
        """
        file = self.get_log_filename()
        filepath = os.path.join(proj.proj_dir, self.mirror_dirname, file)
        js = {}
        if os.path.exists(filepath):
            with open(filepath, "r") as ff:
                js = json.load(ff)
        return js