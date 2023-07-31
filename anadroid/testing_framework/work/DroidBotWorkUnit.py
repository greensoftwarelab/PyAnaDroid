from anadroid.testing_framework.work.WorkUnit import WorkUnit
from anadroid.utils.Utils import execute_shell_command


def convert_arg(key, val):
    if val.lower() == 'true':
        return f' -{key}'
    elif val.lower() == 'false':
        return ''
    else:
        return f' -{key} {val}'


class DroidBotWorkUnit(WorkUnit):
    """extends WorkUnit functionality to adapt it to droidbot framework executions."""
    def __init__(self, bin_cmd):
        super(DroidBotWorkUnit, self).__init__(bin_cmd)
        x = set()

    def execute(self, extras=None, *args, **kwargs):
        cmd = self.command
        if extras:
            cmd = f'{cmd} {extras}'
        print(f"droidbot command: {cmd}")
        execute_shell_command(cmd).validate(("Error executing command " + cmd))

    def config(self, id=None, **kwargs):
        cmd = self.command
        for k, v in kwargs.items():
            cmd += convert_arg(k, v)
        self.command = cmd

    def export_results(self, target_dir=None):
        pass