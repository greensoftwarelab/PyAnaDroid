import os
import shutil

from textops import cut, grep, echo

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.application.AbstractApplication import AbstractApplication
from anadroid.application.AndroidProject import AndroidProject
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.instrument.Types import INSTRUMENTATION_TYPE
from anadroid.utils.Utils import get_date_str, logw, logi


def get_prefix(testing_framework, inst_type):
    """Gets an adequate prefix for a folder, given the testing framework and instrumentation type.

    Args:
        testing_framework (TESTING_FRAMEWORK): Testing framework enumeration.
        inst_type (INSTRUMENTATION_TYPE): Instrumentation type enumeration.

    Returns:
        prefix (str): Prefix for the folder.
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
        device (Device): Device where the app is installed.
        proj (AndroidProject): Respective Android project.
        package_name (str): Package name of the app.
        local_res_dir (str): Local results directory.
        app_name (str): Name of the app.
        version (DefaultSemanticVersion): App version.
    """
    def __init__(self, device, proj, package_name, apk_path, local_res_dir, app_name="app", version=None):
        """Initializes an App instance.

        Args:
            device (Device): Device where the app is installed.
            proj (Project): Respective Android project.
            package_name (str): Package name of the app.
            apk_path (str): Path to the APK.
            local_res_dir (str): Local results directory.
            app_name (str): Name of the app.
            version (DefaultSemanticVersion): App version.
        """
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
        """Initializes the results directory and subdirectories."""
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
        # Copy all methods
        all_m = os.path.join(self.local_res, "all", "allMethods.json")
        if not os.path.exists(all_m):
            all_m_proj = os.path.join(self.proj.proj_dir, "allMethods.json")
            if os.path.exists(all_m_proj):
                print(f"copying {all_m_proj} to {all_m}")
                shutil.copyfile(all_m_proj, all_m)
            else:
                other_possible_all_m = os.path.join(self.local_res, "oldRuns", "all", "allMethods.json")
                if os.path.exists(other_possible_all_m):
                    print(f"copying {other_possible_all_m} to {all_m}")
                    shutil.copyfile(other_possible_all_m, all_m)

    def init_local_test_(self, testing_framework, inst_type):
        """Initializes a directory for a current test being run with the specified testing framework and instrumented with the specified instrumentation type.

        Args:
            testing_framework (TESTING_FRAMEWORK): Testing framework enumeration.
            inst_type (INSTRUMENTATION_TYPE): Instrumentation type enumeration.
        """
        dirname = os.path.join(self.local_res, get_prefix(testing_framework, inst_type))
        os.mkdir(dirname)
        self.curr_local_dir = dirname
        self.proj.save_proj_json(self.curr_local_dir)
        self.device.save_device_specs(os.path.join(self.curr_local_dir, "device.json"))
        self.device.save_device_info(os.path.join(self.curr_local_dir, "deviceState.json"))

    def start(self):
        """Starts the application on the device.

        Starts the app by calling monkey -p <pkg_name> 1.
        """
        self.device.execute_command("monkey -p {pkg} 1".format(pkg=self.package_name), args=[], shell=True)
        self.on_fg = True

    def kill(self):
        """Kills the running app.

        Not yet implemented.
        """
        self.on_fg = False
        pass

    def stop(self):
        """Stops the running app.

        Stops the app via the activity manager (force-stop command).
        """
        self.on_fg = False
        self.device.execute_command(f"am force-stop {self.package_name}",
                                    shell=True) \
            .validate(Exception("error stopping app"))

    def performAction(self, act):
        """Performs an action (Not yet implemented)."""
        pass

    def set_immersive_mode(self):
        """Sets immersive mode for this app if the Android version < 11.

        This feature is only available for devices running Android 10 or lower.
        """
        if self.device.get_device_android_version().major >= 11:
            logw("immersive mode not available on Android 11+ devices")
            return
        logi("setting immersive mode")
        self.device.execute_command(f"settings put global policy_control immersive.full={self.package_name}", shell=True)\
            .validate(Exception("error setting immersive mode"))

    def clean_cache(self):
        """Cleans the app cache.

        Cleans the app cache on the device using the package manager.
        """
        self.device.execute_command(f"pm clear {self.package_name}", shell=True)

    def __get_version(self):
        """Returns the app version.

        Obtains the app version using dumpsys.

        Returns:
            version (DefaultSemanticVersion): App version.
        """
        if isinstance(self.proj, AndroidProject) and self.proj.proj_version != DefaultSemanticVersion("0.0"):
            return self.proj.proj_version
        res = self.device.execute_command(f"dumpsys package {self.package_name}", shell=True)
        if res.validate(Exception("unable to determine version of package")):
            version = echo(res.output | grep("versionName") | cut("=", 1))
            return DefaultSemanticVersion(str(version))

    def get_app_json(self):
        """Get a JSON representation of the app.

        Returns:
            dict: JSON representation of the app.
        """
        return {
            'app_id': self.proj.app_id,
            'app_package': self.package_name,
            'app_version': str(self.version),
            'app_project': self.proj.proj_name,
            'app_language': 'Java'
        }

    def get_permissions_json(self):
        """Get the permissions JSON file.

        Returns:
            str: Path to the permissions JSON file or None if it doesn't exist.
        """
        file_to_look = os.path.join(self.curr_local_dir, "appPermissions.json")
        return None if not os.path.exists(file_to_look) else file_to_look
