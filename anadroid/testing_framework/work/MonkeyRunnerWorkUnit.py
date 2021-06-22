from anadroid.testing_framework.work.WorkUnit import WorkUnit
from anadroid.utils.Utils import execute_shell_command

RUNNER_OPTIONS = {
   'plugin'
}



def convert_arg(key,val):
    if key in RUNNER_OPTIONS:
        return "-" + key + " " + val
    else:
        return "-" + key + " " + val

class MonkeyRunnerWorkUnit(WorkUnit):
    def __init__(self, bin_cmd):
        super(MonkeyRunnerWorkUnit, self).__init__(bin_cmd)

    def execute(self, package_name=None, *args, **kwargs):
        self.command = (self.command + " " + package_name) if package_name is not None else self.command
        for k, v in kwargs.items():
            self.command += " " + convert_arg(k, v)
        for v in args:
            self.command += " " + v
        print("executing command: " + self.command)
        res = execute_shell_command(self.command).validate(Exception("Error running command"))
        if 'log_filename' in kwargs:
            execute_shell_command(f"adb logcat -d > {kwargs['log_filename']}").validate(Exception("Unable to extract device log"))


    def config(self, filepath=None, **kwargs):
        cmd = self.command + " " + filepath if filepath is not None else self.command
        for k, v in kwargs.items():
            cmd += " " + convert_arg(k, v)
        self.command = cmd
