from textops import cut, grep, echo

from src.application.AbstractApplication import AbstractApplication
from src.build.versionUpgrader import DefaultSemanticVersion


class App(AbstractApplication):
    def __init__(self, device, package_name, local_res, name="app", version=None):
        self.device = device

        super(App, self).__init__(package_name, version)
        self.version = self.__get_version() if version is None else version
        self.local_res = local_res + "/" + str(self.version)
        self.name = name


    def start(self):
        self.device.execute_command("monkey -p {pkg} 1".format(pkg=self.package_name), args=[], shell=True)
        self.on_fg = True

    def kill(self):
        self.on_fg = False
        pass

    def stop(self):
        self.on_fg=False
        self.device.execute_command(f"am force-stop {self.package_name}",
                                    shell=True) \
            .validate(Exception("error stopping app"))


    def performAction(self, act):
        pass

    def set_immersive_mode(self):
        if self.device.get_device_android_version() >= 11:
            print("immersive mode not available on Android 11+ devices")
        print("setting immersive mode")
        self.device.execute_command(f"settings put global policy_control immersive.full={self.package_name}",shell=True)\
           .validate(Exception("error setting immersive mode"))

    def clean_cache(self):
        self.device.execute_command(f"pm clear {self.package_name}",shell=True)\
            .validate(Exception("error cleaning cache of package " + self.package_name))

    def __get_version(self):
        res = self.device.execute_command(f"dumpsys package {self.package_name}",shell=True)
        if res.validate(Exception("unable to determinate version of package")):
            version = echo(res.output | grep("versionName") | cut("=",1))
            return DefaultSemanticVersion(str(version))
