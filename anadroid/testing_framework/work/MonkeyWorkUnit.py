from anadroid.testing_framework.work.WorkUnit import WorkUnit
from anadroid.utils.Utils import execute_shell_command

EVENT_OPTIONS = {
    "throttle",
    "pct-touch",
    "pct-motion",
    "pct-trackball",
    "pct-nav",
    "pct-majornav",
    "pct-syskeys",
    "pct-appswitch",
    "pct-anyevent"
}

DEBUGGING_OPTIONS = {
    "dbg-no-events",
    "hprof",
    "ignore-crashes",
    "ignore-timeouts",
    "ignore-security-exceptions",
    "kill-process-after-error",
    "monitor-native-crashes",
    "wait-dbg"
}

DEFAULT_EVENT_COUNT=1000

def convert_arg(key,val):
    if key in DEBUGGING_OPTIONS:
        return "--" + key
    elif key in EVENT_OPTIONS:
        return "--" + key + " " + val
    else:
        print(f"invalid option:-{key}-".format(key=key))
        return ""


class MonkeyWorkUnit(WorkUnit):
    def __init__(self, bin_cmd):
       super(MonkeyWorkUnit, self).__init__(bin_cmd)

    def execute(self, package_name, *args, **kwargs):
        el_commandant = self.command % package_name
        print("executing command: " + el_commandant)
        execute_shell_command(el_commandant).validate(Exception("Error executing command " + el_commandant))
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}").validate(Exception("Unable to extract device log"))

    def config(self, seed=None, **kwargs):
        #adb shell monkey -s $monkey_seed -p $package -v --pct-syskeys 0 --ignore-security-exceptions --throttle $delay_bt_events $monkey_nr_events) &> $localDir/monkey$monkey_seed.log)"
        cmd = self.command
        nr_events = DEFAULT_EVENT_COUNT
        if seed is not None:
            cmd += " -s {seed} ".format(seed=seed)
        if "event-count" in kwargs.keys():
            nr_events = kwargs["event-count"] if 'event_count' in kwargs else nr_events
            kwargs.pop("event-count")
        for k, v in kwargs.items():
            cmd += " " + convert_arg(k, v)

        self.command = cmd + " -p %s " + str(nr_events)

    def export_results(self):
        pass