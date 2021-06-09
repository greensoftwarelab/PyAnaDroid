import os
import time

from manafa.emanafa import EManafa


from src.profiler.AbstractProfiler import AbstractProfiler
from src.utils.Utils import execute_shell_command


class ManafaProfiler(AbstractProfiler):
    def __init__(self, profiler, device, power_profile=None, timezone=None):
        super(ManafaProfiler, self).__init__(profiler,device, pkg_name=None)
        self.manafa = EManafa(power_profile, timezone)
        self.last_bts_file = None
        self.last_pft_file = None
        self.hunter_file = None


    def install_profiler(self):
        pass

    def init(self, **kwargs):
        self.manafa.init()

    def start_profiling(self, tag=""):
        self.manafa.start()

    def stop_profiling(self, tag="", export=False):
        self.last_bts_file, self.last_pft_file, self.hunter_file = self.manafa.stop()

    def update_state(self, val=0, desc="stopped"):
        pass

    def export_results(self, out_filename=None):
        pass

    def pull_results(self, file_id, target_dir):
        cmd = f"cp -r {self.last_bts_file} {self.last_pft_file} {self.hunter_file} {target_dir}"
        execute_shell_command(cmd)\
            .validate(Exception("No result files to pull "))

    def get_dependencies_location(self):
        return []

    def needs_external_dependencies(self):
        return False


