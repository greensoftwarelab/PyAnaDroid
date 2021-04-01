from src.application.Dependency import BuildDependency, DependencyType
from src.profiler.AbstractProfiler import AbstractProfiler


RESOURCES_DIR = "resources"

class TrepnProfiler(AbstractProfiler):

    def __init__(self, device):
        dependency_lib = BuildDependency("TrepnLib-release", DependencyType.LOCAL_BINARY, version=None, bin_type="aar")
        self.local_dep_location = RESOURCES_DIR + "/profilers/Trepn/libsAdded/" + dependency_lib.name + "." + dependency_lib.bin_type #TODO
        super(TrepnProfiler, self).__init__(device, pkg_name="com.quicinc.trepn", device_dir="sdcard/trepn", dependency=dependency_lib)

    def init(self, **kwargs):
        pass

    def start_profiling(self, tag=""):
        pass

    def stop_profiling(self, tag=""):
        pass

    def update_state(self, tag="", desc=""):
        pass

    def export_results(self, filename):
        pass

    def get_dependency_location(self):
        return self.local_dep_location
