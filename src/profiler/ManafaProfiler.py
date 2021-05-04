import os
import time

from manafa.emanafa import EManafa

from src.application.Dependency import BuildDependency, DependencyType
from src.profiler.AbstractProfiler import AbstractProfiler
from manafa.utils.Utils import execute_shell_command, get_results_dir

RESOURCES_DIR = "resources"
MANAFA_RESULTS_DIR = get_results_dir()

class ManafaProfiler(AbstractProfiler):
    def __init__(self, device, power_profile=None, timezone=None, resources_dir=RESOURCES_DIR):
        super(ManafaProfiler, self).__init__(device, pkg_name=None)
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
        execute_shell_command("cp -r {manafa_results_dir}/hunter {results_dir}".format(
            manafa_results_dir=MANAFA_RESULTS_DIR,
            results_dir=target_dir
            )
        )

    def get_dependencies_location(self):
        return []

    def needs_external_dependencies(self):
        return False


