import os
import shutil

from textops import cut, grep, echo

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.application.AbstractApplication import AbstractApplication
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.instrument.Types import INSTRUMENTATION_TYPE
from anadroid.utils.Utils import get_date_str, logw, logi


def get_prefix(testing_framework, inst_type):
    """gets adequate prefix for folder, given the testing framework and instrumentation type
    Args:
        testing_framework:
        inst_type:

    Returns:
        prefix(str): prefix.
    """
    dirname = testing_framework.value
    if inst_type == INSTRUMENTATION_TYPE.METHOD:
        dirname += "Method"
    elif inst_type == INSTRUMENTATION_TYPE.TEST:
        dirname += "Test"
    elif inst_type == INSTRUMENTATION_TYPE.ANNOTATION:
        dirname += "Annotation"
    else:
        raise Exception("Not implemented")
    cur_datetime = get_date_str()
    return dirname + "_"+cur_datetime


class App(AbstractApplication):
    """Main class that abstracts an Android App.
    Attributes:
        device(Device): device where the app is.
        proj(AndroidProject): respective project.
        package_name(str): package name.
        local_res_dir(str): local results dir.
        app_name: name of the app.
        version: app version.
    """
    def __init__(self, device, proj, package_name, apk_path, local_res_dir, app_name="app", version=None):
        self.device = device
        self.proj = proj
        self.apk = apk_path
        super(App, self).__init__(package_name, version)
        self.version = self.__get_version() if version is None else version
        self.local_res = os.path.join(local_res_dir, str(self.version))
        self.name = app_name
        self.curr_local_dir = None
        self.__init_res_dir()
        self.proj.apps.append(self)

    def __init_res_dir(self):
        """initialize results dir and subdirectories."""
        all_dir = os.path.join(self.local_res, "all")
        old_runs_dir = os.path.join(self.local_res, "oldRuns")
        if not os.path.exists(self.local_res):
            os.mkdir(self.local_res)
        if not os.path.exists(all_dir):
            os.mkdir(all_dir)
        if not os.path.exists(old_runs_dir):
            os.mkdir(old_runs_dir)
        for f in os.scandir(self.local_res):
            if f.path != all_dir and f.path != old_runs_dir:
                try:
                    shutil.move(f.path, old_runs_dir)
                except Exception:
                    continue
        #cp all methods
        all_m = os.path.join(self.local_res, "all", "allMethods.json")
        if not os.path.exists(all_m):
            all_m_proj = os.path.join(self.proj.proj_dir, "allMethods.json")
            shutil.copyfile(all_m_proj, all_m)

    def init_local_test_(self, testing_framework, inst_type):
        """initialize directory for a current test being run with testing_framework, with app instrumented with inst_type
        Args:
            testing_framework: testing framework.
            inst_type: instrumentation type.
        """
        dirname = os.path.join(self.local_res, get_prefix(testing_framework, inst_type))
        os.mkdir(dirname)
        self.curr_local_dir = dirname
        self.proj.save_proj_json(self.curr_local_dir)
        self.device.save_device_specs(os.path.join(self.curr_local_dir, "device.json"))
        self.device.save_device_info(os.path.join(self.curr_local_dir, "deviceState.json"))

    def start(self):
        """starts application on device.
        Starts app by calling monkey -p <pgk_name> 1.
        """
        self.device.execute_command("monkey -p {pkg} 1".format(pkg=self.package_name), args=[], shell=True)
        self.on_fg = True

    def kill(self):
        self.on_fg = False
        pass

    def stop(self):
        """stops running app.
        Stops app via activity manager (force-stop command).
        """
        self.on_fg = False
        self.device.execute_command(f"am force-stop {self.package_name}",
                                    shell=True) \
            .validate(Exception("error stopping app"))

    def performAction(self, act):
        pass

    def set_immersive_mode(self):
        """sets immersive mode for this app if Android version < 11.
        This feature is only available for devices running Android 10 or lower.
        """
        if self.device.get_device_android_version().major >= 11:
            logw("immersive mode not available on Android 11+ devices")
            return
        logi("setting immersive mode")
        self.device.execute_command(f"settings put global policy_control immersive.full={self.package_name}", shell=True)\
            .validate(Exception("error setting immersive mode"))

    def clean_cache(self):
        """clean app cache.
        Cleans app cache on device using package manager.
        """
        self.device.execute_command(f"pm clear {self.package_name}", shell=True)#\
            #.validate(Exception("error cleaning cache of package " + self.package_name))

    def __get_version(self):
        """returns app version.
        Obtains app version using dumpsys.
        Returns:
            object(DefaultSemanticVersion): app version.
        """
        if self.proj.proj_version != DefaultSemanticVersion("0.0"):
            return self.proj.proj_version
        res = self.device.execute_command(f"dumpsys package {self.package_name}", shell=True)
        if res.validate(Exception("unable to determinate version of package")):
            version = echo(res.output | grep("versionName") | cut("=", 1))
            return DefaultSemanticVersion(str(version))

    def get_app_json(self):
        return {
            'app_id': self.proj.app_id,
            'app_package': self.package_name,
            'app_version': str(self.version),
            'app_project': self.proj.proj_name,
            'app_language': 'Java'
        }