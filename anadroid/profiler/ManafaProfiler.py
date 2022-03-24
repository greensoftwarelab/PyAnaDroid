import json
import os
import time

from manafa.emanafa import EManafa
from manafa.hunter_emanafa import HunterEManafa

from anadroid.profiler.AbstractProfiler import AbstractProfiler
from anadroid.utils.Utils import execute_shell_command, get_resources_dir

#RESOURCES_DIR = "resources/profilers/Manafa"
RESOURCES_DIR = os.path.join(get_resources_dir(), "profilers", "Manafa")
HUNTER_INSTRUMENT_FILE = os.path.join(RESOURCES_DIR, "to_instrument_file.txt")
HUNTER_NOT_INSTRUMENT_FILE = os.path.join(RESOURCES_DIR, "not_instrument_file.txt")
TEST_INDEX_FILENAME = "tests_index.json"

class ManafaProfiler(AbstractProfiler):
    """Implements AbstractProfiler interface to allow profiling with Manafa profiler.
    Provides a set of methods that allow to manage a profiling session lifecycle.
    Attributes:
        manafa(EManafa): EManafa profiler.
    """
    def __init__(self, profiler, device, power_profile=None, timezone=None, hunter=True):
        super(ManafaProfiler, self).__init__(profiler, device, pkg_name=None)
        self.manafa = EManafa(power_profile, timezone) if not hunter else \
            HunterEManafa(
                power_profile=power_profile,
                timezone=timezone,
                instrument_file=HUNTER_INSTRUMENT_FILE,
                not_instrument_file=HUNTER_NOT_INSTRUMENT_FILE)
        self.test_index_file = TEST_INDEX_FILENAME

    def install_profiler(self):
        res = self.device.execute_command("perfetto -h", shell=True)
        print(res)
        pass

    def init(self, **kwargs):
        self.manafa.init()

    def start_profiling(self, tag=""):
        self.manafa.start()

    def stop_profiling(self, tag="", export=False):
        self.manafa.stop()

    def update_state(self, val=0, desc="stopped"):
        """does nothing."""
        pass

    def export_results(self, out_filename=None):
        """does nothing."""
        pass

    def pull_results(self, test_id, target_dir):
        """pull results from device and put them in target_dir.

        Pulls results from device, place them in target_dir and update tests index.

        """
        hunter_log = ""
        consumptions_log = ""
        da_list = [
            os.path.join(target_dir, os.path.basename(self.manafa.bts_out_file)),
            os.path.join(target_dir, os.path.basename(self.manafa.pft_out_file)),
        ]
        if isinstance(self.manafa, HunterEManafa):
            hunter_log = self.manafa.hunter_out_file
            consumptions_log = self.manafa.app_consumptions_log
            da_list.append( os.path.join(target_dir, os.path.basename(hunter_log)))
            da_list.append(os.path.join(target_dir, os.path.basename(consumptions_log)))
            da_list.append(os.path.join(target_dir, os.path.basename(consumptions_log)))
        cmd = f"cp -r {self.manafa.bts_out_file} {self.manafa.pft_out_file} {hunter_log} {consumptions_log} {target_dir}"
        execute_shell_command(cmd)\
            .validate(Exception("No result files to pull"))
        # update or create test index
        test_index_file = os.path.join(target_dir, self.test_index_file)
        js = {}
        if os.path.exists(test_index_file):
            #update file
            with open(test_index_file, 'w') as jj:
                js = json.load(jj)
        js[str(test_id)] = da_list
        with open(test_index_file, 'w') as jj:
            json.dump(js, jj)

    def get_dependencies_location(self):
        return []

    def needs_external_dependencies(self):
        return False


