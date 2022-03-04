from anadroid.utils.Utils import execute_shell_command


class WorkUnit(object):
    """Provides a reference implementation to store information about a work unit.
    A work unit is a command or task to be performed in a context of a test or test suite to be performed by a testing
    framework command.
    Attributes:
        command(str): command to be executed.
        cmd_args(dict): set os keyed args to appended to command.
        has_timeout(bool): True if the command has time limit to execute, False otherwise.
    """
    def __init__(self, bin_cmd):
        self.command = bin_cmd
        self.cmd_args = {}
        self.has_timeout = False

    def execute(self, pkg_name, *args, **kwargs):
        """execute the current work unit for a given app identified by package name.
        Args:
            pkg_name(str): package name.
        """
        self.command = self.command + pkg_name
        print("executing command " + self.command)
        res = execute_shell_command(self.command)
        res.validate(Exception("Error executing command " + self.command))

    def build_command(self,  pkg_name, *args, **kwargs):
        """build command for a given app identified by package name.
        Args:
            pkg_name(str): package name.
        """
        self.command = self.command % pkg_name if "%" in self.command else self.command + " " + pkg_name
        if 'timeout' in kwargs and not self.has_timeout:
            self.add_timeout(kwargs.get('timeout'))
        return self.command

    def add_timeout(self, timeout_val):
        """adds a timeout to the work unit.
        Args:
            timeout_val(int): timeout value in seconds.
        """
        if not self.has_timeout:
            self.command = f"timeout {timeout_val} {self.command}"
            self.has_timeout = True

    def config(self, id=None, *args, **kwargs):
        """configure command.
        Args:
            id: run or app id.
        """
        #adb shell monkey -s $monkey_seed -p $package -v --pct-syskeys 0 --ignore-security-exceptions --throttle $delay_bt_events $monkey_nr_events) &> $localDir/monkey$monkey_seed.log)"
        cmd = self.command + " "
        cmd += "" if id is None else id
        for k, v in kwargs.items():
            cmd += f' {k} {v}'
        self.command = cmd

    def export_results(self, target_dir=None):
        """export results from work unit.
        Args:
            target_dir: directory where the results will be exported.
        """
        pass

    def append_prefix(self, prefix):
        """adds prefix to command."""
        self.command = prefix + " " + self.command