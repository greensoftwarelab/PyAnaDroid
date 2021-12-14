import argparse
from enum import Enum

from anadroid.Anadroid import AnaDroid
from anadroid.Types import TESTING_FRAMEWORK, PROFILER, ANALYZER, INSTRUMENTER
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.device.MockedDevice import MockedDevice
from anadroid.instrument.Types import INSTRUMENTATION_TYPE


def init_PyAnaDroid(args):
    return AnaDroid(apps_dir=args.diretory,
                      testing_framework=TESTING_FRAMEWORK(args.testingframework),
                      device=MockedDevice() if args.buildonly or args.justanalyze else None,
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
    parser.add_argument("-d", "--diretory", default="demoProjects", type=str, help="app(s)' folder")
    parser.add_argument("-bi", "--buildonly", help="just build apps", action='store_true')
    parser.add_argument("-r", "--record", help="record test", action='store_true')
    parser.add_argument("-ri", "--reinstall", help="reinstall apks", action='store_true')
    parser.add_argument("-ja", "--justanalyze", help="just analyze apps", action='store_true')
    args = parser.parse_args()
    anadroid = init_PyAnaDroid(args)
    if args.buildonly:
        anadroid.just_build_apps()
    elif args.justanalyze:
        raise NotImplementedError()
        anadroid.just_analyze()
    elif args.record:
        anadroid.record_tests()
    else:
        anadroid.defaultWorkflow()