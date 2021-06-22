import os
import time

from manafa.emanafa import EManafa
from manafa.hunter_emanafa import HunterEManafa

from anadroid.profiler.AbstractProfiler import AbstractProfiler
from anadroid.utils.Utils import execute_shell_command


class ManafaProfiler(AbstractProfiler):
    def __init__(self, profiler, device, power_profile=None, timezone=None, hunter=True):
        super(ManafaProfiler, self).__init__(profiler, device, pkg_name=None)
        self.manafa = EManafa(power_profile, timezone) if not hunter else HunterEManafa(power_profile, timezone)


    def install_profiler(self):
        pass

    def init(self, **kwargs):
        self.manafa.init()

    def start_profiling(self, tag=""):
        self.manafa.start()

    def stop_profiling(self, tag="", export=False):
        self.manafa.stop()

    def update_state(self, val=0, desc="stopped"):
        pass

    def export_results(self, out_filename=None):
        pass

    def pull_results(self, file_id, target_dir):
        also_hunter = self.manafa.hunter_out_file if isinstance(self.manafa,HunterEManafa) else ""
        cmd = f"cp -r {self.manafa.bts_out_file} {self.manafa.pft_out_file} {also_hunter} {target_dir}"
        execute_shell_command(cmd)\
            .validate(Exception("No result files to pull "))

    def get_dependencies_location(self):
        return []

    def needs_external_dependencies(self):
        return False


