import os, time

from textops import find, grep, sed, head

from src.application.AndroidProject import AndroidProject, BUILD_TYPE
from src.application.Application import App
from src.build.GradleBuilder import GradleBuilder

from src.device.Device import Device, get_first_connected_device
from src.instrument.JInstInstrumenter import JInstInstrumenter
from src.profiler.TrepnProfiler import TrepnProfiler
from src.testing_framework.MonkeyFramework import MonkeyFramework
from src.utils.Utils import execute_shell_command, mega_find
from src.view.cli.CliView import CLIView
from src import Types

MIN_API_LEVEL = 9
MAX_API_LEVEL = 30


def do_work(device, pkgs, tf, profiler):
    for i, pkg in enumerate(pkgs):
        print("testing package " + pkg)
        app = App(device, pkg)
        for wk_unit in tf.workload:
            device.unlock_screen()
            profiler.init()
            profiler.start_profiling()
            app.start()
            tf.execute_test(wk_unit)
            app.stop()


def defaultWorkflow(apps_folder):
    tf = MonkeyFramework(default_workload=True)
    view = CLIView()
    device = get_first_connected_device()
    profiler = TrepnProfiler(device)
    inst = JInstInstrumenter(profiler)

    app_projects = filter(lambda x: os.path.isdir(os.path.join(apps_folder, x)), os.listdir(apps_folder))
    for app_name in app_projects:
        original_proj = AndroidProject(projname=app_name, projdir=apps_folder+"/"+app_name)
        instrumented_proj_dir = inst.instrument(original_proj)
        instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir)
        builder = GradleBuilder(instr_proj, device, "resources", inst)
        builder.build_proj_and_apk(build_type=BUILD_TYPE.RELEASE)
        installed_pkgs = device.install_apks(instr_proj)

        do_work(device, installed_pkgs, tf, profiler)
        for pkg in installed_pkgs:
            print("uninstalling " + pkg)
            device.uninstall_pkg(pkg)



    # Press the green button in the gutter to run the script.
if __name__ == '__main__':
    apps_folder = "/Users/ruirua/repos/Anadroid/demoProjects/"
    defaultWorkflow(apps_folder)