from anadroid.Anadroid import AnaDroid
from anadroid.Types import PROFILER, TESTING_FRAMEWORK, INSTRUMENTER, BUILD_SYSTEM, ANALYZER
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.build.NaiveGradleBuilder import NaiveGradleBuilder
from anadroid.instrument.Types import INSTRUMENTATION_TYPE
from anadroid.utils.Utils import get_results_dir


class AnadroidWithNaiveBuilder(AnaDroid):
    def __init__(self, arg1, results_dir=get_results_dir(), profiler=PROFILER.MANAFA,
                 testing_framework=TESTING_FRAMEWORK.MONKEY, device=None, instrumenter=INSTRUMENTER.JINST,
                 analyzer=ANALYZER.OLD_ANADROID_ANALYZER, instrumentation_type=INSTRUMENTATION_TYPE.ANNOTATION,
                 build_system=BUILD_SYSTEM.GRADLE, build_type=BUILD_TYPE.DEBUG, tests_dir=None, rebuild_apps=False,
                 reinstrument=False):
        super(AnadroidWithNaiveBuilder, self).__init__(arg1, results_dir=results_dir, profiler=profiler,
                 testing_framework=testing_framework, device=device, instrumenter=instrumenter,
                 analyzer=analyzer, instrumentation_type=instrumentation_type,
                 build_system=build_system, build_type=build_type, tests_dir=tests_dir, rebuild_apps=rebuild_apps,
                 reinstrument=reinstrument)


    def init_builder(self, instr_proj):
        if self.builder == BUILD_SYSTEM.GRADLE:
            print("naive builder")
            return NaiveGradleBuilder(instr_proj, self.device, self.resources_dir, self.instrumenter)
        return None