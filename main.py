import os

from src.instrument.JInstInstrumenter import JInstInstrumenter
from src.view.cli.CliView import CLIView
from src import Types

MIN_API_LEVEL = 9
MAX_API_LEVEL = 30

def defaultWorkflow(app_folder):
    tf = "monkey"
    pf = "trepn"
    inst = JInstInstrumenter()
    view = CLIView()
    device_serial = os.popen('adb devices -l  | grep \"product\" | cut -f1 -d\ ').read().split("\n")[0] # TODO replace by method call that gives fst device serial found
    app_projects = filter(lambda x: os.path.isdir(os.path.join(app_folder, x)), os.listdir(app_folder))
    for app_dir in app_projects:
        instrumented_app = inst.instrument(proj_dir=app_folder+"/"+app_dir, main_manifest=app_folder+"/"+app_dir+"/app/src/main/AndroidManifest.xml",app_id="appaaa")
        print(instrumented_app)

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app_folder = "/Users/ruirua/repos/Anadroid/demoProjects"
    defaultWorkflow(app_folder)

