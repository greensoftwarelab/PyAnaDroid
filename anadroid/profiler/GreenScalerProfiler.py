import os
import subprocess
import time
from enum import Enum

from anadroid.profiler.AbstractProfiler import AbstractProfiler
from anadroid.profiler.greenScaler.GreenScaler.greenscaler import cpu_measurement, get_foreground_app, syscall_trace, \
    screen_capture
from anadroid.profiler.greenScaler.GreenScaler.libmutation import greenscalerapplication, model
from anadroid.profiler.greenScaler.GreenScaler.libmutation.greenscalerapplication import GreenScalerApplication
from anadroid.utils.Utils import execute_shell_command

DEFAULT_RES_DIR="resources/profilers/GreenScaler"

class GREENSCALER_TASK(Enum):
    CPU_PROFILING = "CPU Profiling"
    SYSTRACE = "Syscal Tracing"
    SCREEN_CAPTURE = "Screen Capture"


class GreenScalerProfiler(AbstractProfiler):
    def __init__(self, profiler, device, resources_dir=DEFAULT_RES_DIR):
        #if not device.is_rooted():
        #    raise Exception("GreenScaler cannot be used in noon-rooted devices")
        super(GreenScalerProfiler, self).__init__(profiler,device, pkg_name=None)
        self.resources_dir = resources_dir
        if self.__is_installed():
            self.install_profiler()
        self.inner_app = None

    def __is_installed(self):
        res = self.device.execute_command("ls sdcard ", shell=True)
        if res.validate(Exception("Error obtained while device sdcard content")):
            return "cpu_after.sh" in res.output
        return False

    def install_profiler(self):
        path_of_installer = os.path.join(self.resources_dir, "push_to_phone", "push.sh")
        print(path_of_installer)
        execute_shell_command(path_of_installer).validate(Exception("Unable to install GreenScaler"))


    def init(self, **kwargs):
        pynadroid_app = kwargs.get("app") if "app" in kwargs else None
        self.inner_app = GreenScalerApplication(pynadroid_app.name, pynadroid_app.package_name)

    def start_profiling(self, task=GREENSCALER_TASK.CPU_PROFILING):
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

    def exec_greenscaler(self, package, test_cmd, runs=1):
        n = runs
        app = greenscalerapplication.GreenScalerApplication(package, package, runTestCommand=exec_command)
        print("executing test")
        cpu_measurement(app, package, n, package, test_cmd)
        foreground_app = get_foreground_app()
        print("-" + foreground_app + "-")
        if foreground_app != package:
            print("Error detected. App crashed or stopped during execution")
            return
        app.stop_and_clean_app()
        print("capture system calls")
        syscall_trace(app, package, n, package, test_cmd)
        foreground_app = get_foreground_app()
        if foreground_app != package:
            print("Error detected. App crashed or stopped during execution")
            return
        app.stop_and_clean_app()
        print("Now run to capture screen shots")
        n_tries = 5
        while n_tries > 0:
            n_tries = n_tries - 1
            app.stop_and_clean_app()
            n_image = screen_capture(app, package, n, package, test_cmd)
            if n_image == 1:
                break
        energy = model.estimate_energy(package, app, n)
        print("Energy = " + str(energy) + " Joules")
        app.stop_and_clean_app()

def exec_command(self, command):
    pipes = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    std_out, std_err = pipes.communicate()

    if pipes.returncode != 0:
        # an error happened!
        err_msg = "%s. Code: %s" % (std_err.strip(), pipes.returncode)
        raise Exception(err_msg)

    elif len(std_err):
        print(std_out)
    # return code is 0 (no error), but we may want to
    # do something with the info on std_err
    # i.e. logger.warning(std_err)