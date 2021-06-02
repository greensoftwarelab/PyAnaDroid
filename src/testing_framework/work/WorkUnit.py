from src.utils.Utils import execute_shell_command


class WorkUnit(object):
    def __init__(self, bin_cmd):
        self.command = bin_cmd
        self.cmd_args = {}


    def execute(self,pkg_name, **kwargs):
        self.command = self.command + pkg_name
        print("excuting command " + self.command)
        res = execute_shell_command(self.command)
        res.validate(Exception("Error executing command " + self.command))

    def config(self, id=None, *args, **kwargs):
        #adb shell monkey -s $monkey_seed -p $package -v --pct-syskeys 0 --ignore-security-exceptions --throttle $delay_bt_events $monkey_nr_events) &> $localDir/monkey$monkey_seed.log)"
        cmd = self.command + " "
        cmd += "" if id is None else id
        for k, v in kwargs.items():
            cmd += " ".join(v)
        self.command = cmd

    def export_results(self):
        pass