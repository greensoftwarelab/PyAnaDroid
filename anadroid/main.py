import argparse
from enum import Enum

from anadroid.Anadroid import AnaDroid
from anadroid.Types import TESTING_FRAMEWORK, PROFILER, ANALYZER, INSTRUMENTER
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.instrument.Types import INSTRUMENTATION_TYPE


def init_PyAnaDroid(args):
    return AnaDroid(apps_dir=args.folder,
                      testing_framework=TESTING_FRAMEWORK(args.testingframework),
                      profiler=PROFILER(args.profiler),
                      build_type=BUILD_TYPE(args.buildtype),
                      instrumenter=INSTRUMENTER(args.instrumenter),
                      instrumentation_type=INSTRUMENTATION_TYPE(args.instrumentationtype),
                      analyzer=ANALYZER(args.analyzer)
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--testingframework", default=TESTING_FRAMEWORK.MONKEY.value, type=str,
                        help="testing framework to exercise app(s)", choices=[e.value for e in TESTING_FRAMEWORK])
    parser.add_argument("-p", "--profiler", default=PROFILER.MANAFA.value, type=str,
                        help="energy profiler", choices=[e.value for e in PROFILER])
    parser.add_argument("-b", "--buildtype", default=BUILD_TYPE.DEBUG.value, type=str,
                        help="app build type", choices=[e.value for e in BUILD_TYPE])
    parser.add_argument("-i", "--instrumenter", default=INSTRUMENTER.JINST.value, type=str,
                        help="Source code instrumenter", choices=[e.value for e in INSTRUMENTER])
    parser.add_argument("-it", "--instrumentationtype", default=INSTRUMENTATION_TYPE.ANNOTATION.value, type=str,
                        help="instrumentation type", choices=[e.value for e in INSTRUMENTATION_TYPE])
    parser.add_argument("-a", "--analyzer", default=ANALYZER.MANAFA_ANALYZER.value, type=str, help="results analyzer",
                        choices=[e.value for e in INSTRUMENTATION_TYPE])
    parser.add_argument("-f", "--folder", default="demoProjects", type=str, help="apps folder")
    args = parser.parse_args()
    folder_of_apps = "demoProjects/ProgressBars-2.0.0"
    anadroid = init_PyAnaDroid(args)
    #anadroid.defaultWorkflow()
    anadroid.just_build_apps()
