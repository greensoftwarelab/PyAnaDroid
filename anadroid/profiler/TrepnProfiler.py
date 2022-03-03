import os
import time
from shutil import copyfile

from anadroid.application.Dependency import BuildDependency, DependencyType
from anadroid.profiler.AbstractProfiler import AbstractProfiler
from anadroid.utils.Utils import execute_shell_command, get_resources_dir

RESOURCES_DIR = get_resources_dir()
DEFAULT_FILENAME = "trepnfile"
DEFAULT_PREF_FILE = "/sdcard/trepn/saved_preferences/All.pref"
DEFAULT_APK_LOCATION= os.path.join(RESOURCES_DIR, "profilers", "Trepn", "apks", "com.quicinc.trepn-6.2-APK4Fun.com.apk")
DEFAULT_PREFS_DIR= os.path.join(RESOURCES_DIR, "profilers", "Trepn", "TrepnPreferences")
DEFAULT_LAST_RUN_FILE="last_run_duration.log"
EXPORT_THRESHOLD = 0.5


class TrepnProfiler(AbstractProfiler):
    """Implements AbstractProfiler interface to allow profiling with Trepn profiler and TrepnLib.
    Provides a set of methods that allow to manage a profiling session lifecycle.
    Attributes:
        local_dep_location(str): location of trepn apk.
    """
    def __init__(self, profiler, device):
        dependency_lib = BuildDependency("TrepnLib-release", DependencyType.LOCAL_BINARY, version=None, bin_type="aar")
        self.local_dep_location = os.path.join(RESOURCES_DIR, "profilers", "Trepn","libsAdded",  dependency_lib.name + "." + dependency_lib.bin_type) #TODO
        self.start_time = 0
        super(TrepnProfiler, self).__init__(profiler, device, pkg_name="com.quicinc.trepn", device_dir="sdcard/trepn", dependency=dependency_lib)
        if not device.has_package_installed(self.pkg_name):
            self.install_profiler()
        if not device.contains_file(self.device_dir+"/GDFlag"):
            self.setup_trepn_device_dir()

    def install_profiler(self, apk_loc=DEFAULT_APK_LOCATION):
        """install trepn profiler on device.
        Args:
            apk_loc: apk location.
        """
        print("installing trepn")
        self.device.execute_command(f"install -g -r {apk_loc}").validate(Exception("Unable to install Trepn Profiler"))

    def setup_trepn_device_dir(self):
        """setup directory on device where results will be temporarly stored."""
        trepn_dir = self.device_dir
        self.device.execute_command(
            f"mkdir -p {trepn_dir} {trepn_dir}/Traces {trepn_dir}/Measures {trepn_dir}/TracedTests", shell=True)
        prefs_dir = DEFAULT_PREFS_DIR
        # push files: TODO this is not working. ignore for now (push is blocking )
        #self.device.execute_command(f"push {prefs_dir} {trepn_dir}/").validate(Exception("error pushing trepn prefs"))
        self.device.execute_command(f"\"echo 0 > {trepn_dir}/GDFlag\"", shell=True)

    def init(self, **kwargs):
        # start trepn app - trepn app to foreground -> start service -> put app in background
        self.device.execute_command("monkey -p {pkg} -c android.intent.category.LAUNCHER 1".format(pkg=self.pkg_name), args=[], shell=True).validate(Exception("Profiling error"))
        time.sleep(2)
        self.device.execute_command("am startservice --user 0 {pkg}/.TrepnService".format(pkg=self.pkg_name), args=[], shell=True).validate(Exception("Profiling error"))
        time.sleep(3)
        self.device.execute_command("am start -a android.intent.action.MAIN -c android.intent.category.HOME", args=[], shell=True).validate()

    def start_profiling(self, tag=""):
        """starts trepn service."""
        # (adb shell am broadcast -a com.quicinc.trepn.start_profiling -e com.quicinc.trepn.database_file "myfile")
        self.start_time = int(self.device.execute_command("date +%s", shell=True).output)
        self.device.execute_command("am broadcast -a {pkg}.start_profiling -e {pkg}.database_file {filename}".format(pkg=self.pkg_name,filename=DEFAULT_FILENAME), args=[], shell=True).validate(Exception("Profiling error"))


    def stop_profiling(self, tag="", export=False):
        """stops trepn service."""
        self.update_state()
        self.device.execute_command("am broadcast -a {pkg}.stop_profiling".format(pkg=self.pkg_name), args=[], shell=True).validate(Exception("Profiling error: stop profiling"))
        self.log_run_duration()
        time.sleep(5)
        if export:
            self.export_results()

    def update_state(self, val=0, desc="stopped"):
        """updates state of trepn using activity manager."""
        # adb shell am broadcast -a com.quicinc.Trepn.UpdateAppState -e com.quicinc.Trepn.UpdateAppState.Value 1 -e com.quicinc.Trepn.UpdateAppState.Value.Desc "started"
        res = self.device.execute_command("am broadcast -a {pkg}.UpdateAppState -e {pkg}.UpdateAppState.Value {val} -e {pkg}.UpdateAppState.Value.Desc \"{desc}\"".format(pkg=self.pkg_name,val=val,desc=desc),shell=True).validate(Exception("Error updating trepn state"))

    def export_results(self, out_filename="trepnfile.csv"):
        """export results of the previous profiing session.
        Args:
            out_filename: output filepath.
        Returns:
            out_filename: output filepath.
        """
        run_duration = self.get_last_run_duration()
        res = self.device.execute_command("am broadcast -a  {pkg}.export_to_csv -e  {pkg}.export_db_input_file {filename} -e {pkg}.export_csv_output_file {outfile}".format(pkg=self.pkg_name,filename=DEFAULT_FILENAME, outfile=out_filename), args=[], shell=True )
        res.validate(Exception("error while exporting results"))
        time_to_sleep = run_duration * EXPORT_THRESHOLD
        time.sleep(int(time_to_sleep))

        return out_filename

    def pull_results(self, file_id, target_dir):
        """pull results from file"""
        device_filepath = self.device_dir + "/" + file_id
        self.device.execute_command("pull", args=[device_filepath, target_dir], shell=False).validate(Exception("error pulling results"))
        all_dir = os.path.join(target_dir, "..", "all")

    def get_dependencies_location(self):
        return [self.local_dep_location]

    def load_preferences_file(self, pref_file=None):
        """load trepn preferences file containing the list of resources to profile."""
        if pref_file is None:
            pref_file = DEFAULT_PREF_FILE
        self.device.execute_command("am broadcast -a {pkg}.load_preferences -e {pkg}.load_preferences_file {pref_file}".format(pkg=self.pkg_name,pref_file=pref_file),shell=True).validate(Exception("error loading pref file " + pref_file))

    def setup_device_dir(self):
        pass

    def needs_external_dependencies(self):
        return True

    def get_last_run_duration(self):
        last_dur_file = self.device_dir + "/" + DEFAULT_LAST_RUN_FILE
        file_ctent = self.device.execute_command(f"cat {last_dur_file}", shell=True).output.strip()
        try:
            val = int(file_ctent)

        except Exception:
            val = 10
        return val

    def log_run_duration(self):
        cur_time = int(self.device.execute_command("date +%s", shell=True).output)
        run_duration = cur_time - self.start_time
        last_dur_file = self.device_dir + "/" + DEFAULT_LAST_RUN_FILE
        self.device.execute_command(f"\"echo {run_duration} > {last_dur_file}\"", shell=True).validate(Exception("error logging run time"))