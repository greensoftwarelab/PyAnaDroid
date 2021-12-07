import os
import shutil

from textops import cut, grep, echo

from anadroid.Types import TESTING_FRAMEWORK
from anadroid.application.AbstractApplication import AbstractApplication
from anadroid.build.versionUpgrader import DefaultSemanticVersion
from anadroid.instrument.Types import INSTRUMENTATION_TYPE
from anadroid.utils.Utils import get_date_str


def get_prefix(testing_framework, inst_type):
    dirname = testing_framework.value
    if inst_type == INSTRUMENTATION_TYPE.METHOD:
        dirname+="Method"
    elif inst_type == INSTRUMENTATION_TYPE.TEST:
        dirname += "Test"
    elif inst_type == INSTRUMENTATION_TYPE.ANNOTATION:
        dirname += "Annotation"
    else:
        raise Exception("Not implemented")
    cur_datetime = get_date_str()
    return dirname + "_"+cur_datetime




class App(AbstractApplication):
    def __init__(self, device, proj, package_name, apk_path, local_res, name="app", version=None):
        self.device = device
        self.proj = proj
        self.apk = apk_path
        super(App, self).__init__(package_name, version)
        self.version = self.__get_version() if version is None else version
        self.local_res = os.path.join( local_res, str(self.version))
        self.name = name
        self.curr_local_dir = None
        self.__init_res_dir()


    def __init_res_dir(self):
        all_dir = self.local_res+"/all"
        old_runs_dir = self.local_res+"/oldRuns"
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
        if not os.path.exists(all_dir + "/allMethods.json"):
            shutil.move(os.path.join( self.proj.proj_dir , "allMethods.json"), all_dir)

    def init_local_test_(self, testing_framework, inst_type):
        dirname = self.local_res + "/"+ get_prefix(testing_framework,inst_type)
        os.mkdir(dirname)
        self.curr_local_dir = dirname

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
        if self.device.get_device_android_version().major >= 11:
            print("immersive mode not available on Android 11+ devices")
        print("setting immersive mode")
        self.device.execute_command(f"settings put global policy_control immersive.full={self.package_name}",shell=True)\
           .validate(Exception("error setting immersive mode"))

    def clean_cache(self):
        self.device.execute_command(f"pm clear {self.package_name}",shell=True)#\
            #.validate(Exception("error cleaning cache of package " + self.package_name))

    def __get_version(self):
        res = self.device.execute_command(f"dumpsys package {self.package_name}",shell=True)
        if res.validate(Exception("unable to determinate version of package")):
            version = echo(res.output | grep("versionName") | cut("=",1))
            return DefaultSemanticVersion(str(version))
