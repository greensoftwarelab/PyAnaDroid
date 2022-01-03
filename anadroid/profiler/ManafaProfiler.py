import os
import time

from manafa.emanafa import EManafa
from manafa.hunter_emanafa import HunterEManafa

from anadroid.profiler.AbstractProfiler import AbstractProfiler
from anadroid.utils.Utils import execute_shell_command

RESOURCES_DIR = "resources/profilers/Manafa"
HUNTER_INSTRUMENT_FILE = os.path.join(RESOURCES_DIR, "to_instrument_file.txt")
HUNTER_NOT_INSTRUMENT_FILE = os.path.join(RESOURCES_DIR, "not_instrument_file.txt")

class ManafaProfiler(AbstractProfiler):
    def __init__(self, profiler, device, power_profile=None, timezone=None, hunter=True):
        super(ManafaProfiler, self).__init__(profiler, device, pkg_name=None)
        self.manafa = EManafa(power_profile, timezone) if not hunter else \
            HunterEManafa(
                power_profile=power_profile,
                timezone=timezone,
                instrument_file=HUNTER_INSTRUMENT_FILE,
                not_instrument_file=HUNTER_NOT_INSTRUMENT_FILE)


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
        hunter_log = ""
        consumptions_log = ""
        if isinstance(self.manafa, HunterEManafa):
            hunter_log = self.manafa.hunter_out_file
            consumptions_log = self.manafa.app_consumptions_log
        cmd = f"cp -r {self.manafa.bts_out_file} {self.manafa.pft_out_file} {hunter_log} {consumptions_log} {target_dir}"
        execute_shell_command(cmd)\
            .validate(Exception("No result files to pull "))

    def get_dependencies_location(self):
        return []

    def needs_external_dependencies(self):
        return False


