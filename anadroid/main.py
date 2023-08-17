import argparse
import inspect

from anadroid.Anadroid import AnaDroid
from anadroid.Config import set_general_config
from anadroid.Types import TESTING_FRAMEWORK, PROFILER, ANALYZER, INSTRUMENTER
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.device.Device import set_device_conn, Device, has_connected_device
from anadroid.device.MockedDevice import MockedDevice
from anadroid.instrument.Types import INSTRUMENTATION_TYPE


def init_PyAnaDroid_from_args(args):
    needs_dynamic_execution = not (args.buildonly or args.justanalyze or args.device)
    return AnaDroid(arg1=args.diretory if (len(args.package_names) + len(args.application_packages) == 0) else args,
                    testing_framework=TESTING_FRAMEWORK(args.testingframework if needs_dynamic_execution else "None"),
                    device=MockedDevice() if not needs_dynamic_execution and not has_connected_device() else None,
                    profiler=PROFILER(args.profiler if needs_dynamic_execution else PROFILER.NONE),
                    build_type=BUILD_TYPE(args.buildtype),
                    instrumenter=INSTRUMENTER(args.instrumenter),
                    instrumentation_type=INSTRUMENTATION_TYPE(args.instrumentationtype),
                    analyzer=ANALYZER(args.analyzer),
                    tests_dir=args.tests_dir,
                    rebuild_apps=args.rebuild,
                    reinstrument=args.reinstrument,
                    recover_from_last_run=args.recover,
                    test_cmd=args.command,
                    load_projects=not args.run_only
                    )


def process_general_config(args_obj):
    n_times = args_obj.n_times if args_obj.n_times != 0 else 0
    if n_times != 0:
        set_general_config('tests', 'tests_per_app', n_times)


def count_positional_args(func):
    sig = inspect.signature(func)
    positional_args = [param for param in sig.parameters.values()
                       if param.default == inspect.Parameter.empty
                       and param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD]
    return len(positional_args)


def exec_device_cmd(anad, cmd: str):
    device_methods = list(filter(lambda x: not '__' in x, dir(anad.device)))
    has_arg = len(cmd.split(" ")) > 1
    #print(*cmd.split(" "))
    action = cmd.split(" ")[0]
    if action.strip() == 'list':
        action_explanation = list(map(lambda x:
                                      f'-> {x}: ' + getattr(anad.device, x).__doc__.replace("\n", " ")
                                      if getattr(anad.device, x).__doc__ is not None else f'-> {x}', device_methods))
        res = "List of available actions:\n" + "\n".join(action_explanation)
        print(res)
        return res
    try:
        action_m = getattr(anad.device, action)
    except:
        raise Exception(f"Unable to find {action} action")
    min_action_args = count_positional_args(action_m)
    hasnt_enough_arg = callable(action_m) and min_action_args > len(cmd.split(" ")[1:])
    if hasnt_enough_arg:
        raise Exception(f"Not enough args for {action} action. Expecting {min_action_args} args")
    res = action_m if not callable(action_m) else (action_m(*cmd.split(" ")[1:]) if has_arg else action_m())
    print(res)
    return res


def get_device_cmd_help_text():
    return """device <Action> perform device commands"""


def main():
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
    parser.add_argument("-dev", "--device", default=None, type=str,
                        help="device <Action>. performs device class commands")
    parser.add_argument("-bo", "--buildonly", help="just build apps", action='store_true')
    parser.add_argument("-record", "--record", help="record test", action='store_true', default=False)
    parser.add_argument("-run", "--run_only", help="run only", action='store_true')
    #parser.add_argument("-rt", "--retry", help="retry build if previously failed", action='store_true')
    parser.add_argument("-rb", "--rebuild", help="rebuild apps", action='store_true')
    parser.add_argument("-ri", "--reinstrument", help="reinstrument app", action='store_true')
    parser.add_argument("-ja", "--justanalyze", help="just analyze apps", action='store_true')
    #parser.add_argument("-c", "--connection", help="connection to device", choices=["USB", "WIFI"], default="USB")
    parser.add_argument("-sc", "--setconnection", help="set connection to device and exit", choices=["USB", "WIFI"])
    parser.add_argument("-ds", "--device_serial", help="device serial id", type=int, default=None)
    parser.add_argument("-td", "--tests_dir", help="tests directory", type=str, default=None)
    parser.add_argument("-n", "--package_names", help="package(s) of already installed apps", nargs='+', default=[])
    parser.add_argument("-apk", "--application_packages", help="path of apk(s) to process", nargs='+', default=[])
    parser.add_argument("-rec", "--recover", help="recover progress of the previous run", action='store_true')
    parser.add_argument("-cmd", "--command", help="test command", type=str, default=None)
    parser.add_argument("-nt", "--n_times", help="times to repeat test (overrides config)", type=int, default=0)
    args = parser.parse_args()
    process_general_config(args)
    if args.setconnection:
        set_device_conn(args.setconnection, device_id=args.device_serial)
        exit(0)
    anadroid = init_PyAnaDroid_from_args(args)
    if args.device:
        exec_device_cmd(anadroid, args.device)
    elif args.buildonly:
        anadroid.just_build_apps()
    elif args.justanalyze:
        anadroid.just_analyze()
    elif args.record:
        anadroid.record_test(args.tests_dir)
    elif args.run_only:
        anadroid.exec_command()
    else:
        anadroid.default_workflow()


if __name__ == '__main__':
    main()
