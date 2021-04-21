import os
import time

from manafa.emanafa import EManafa

from src.application.Dependency import BuildDependency, DependencyType
from src.profiler.AbstractProfiler import AbstractProfiler

RESOURCES_DIR = "resources"


class ManafaProfiler(AbstractProfiler):
    def __init__(self, device, power_profile=None, timezone=None, resources_dir=RESOURCES_DIR):
        super(ManafaProfiler, self).__init__(device, pkg_name=None)
        self.manafa = EManafa(power_profile, timezone, resources_dir)
        self.last_bts_file = None
        self.last_pft_file = None


    def install_profiler(self):
        pass

    def init(self, **kwargs):
        self.manafa.init()

    def start_profiling(self, tag=""):
       self.manafa.start()

    def stop_profiling(self, tag="", export=False):
        self.last_bts_file, self.last_pft_file = self.manafa.stop()

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


