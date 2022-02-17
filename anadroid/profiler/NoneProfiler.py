import os

from anadroid.profiler.AbstractProfiler import AbstractProfiler
from anadroid.utils.Utils import execute_shell_command, get_resources_dir


class NoneProfiler(AbstractProfiler):
    def __init__(self, profiler, device, power_profile=None, timezone=None, hunter=True):
        super(NoneProfiler, self).__init__(profiler, device, pkg_name=None)

    def install_profiler(self):
        pass

    def init(self, **kwargs):
        pass

    def start_profiling(self, tag=""):
        pass

    def stop_profiling(self, tag="", export=False):
        pass

    def update_state(self, val=0, desc="stopped"):
        pass

    def export_results(self, out_filename=None):
        pass

    def pull_results(self, file_id, target_dir):
        pass

    def get_dependencies_location(self):
        return []

    def needs_external_dependencies(self):
        return False


