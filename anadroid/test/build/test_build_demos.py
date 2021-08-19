import os
from unittest import TestCase

from textops import cat, grep

from anadroid.application.AndroidProject import AndroidProject
from anadroid.device.Device import get_first_connected_device
from anadroid.instrument.Types import INSTRUMENTATION_TYPE
from anadroid.utils.Utils import mega_find
from anadroid.main import init_PyAnaDroid


class TestBuildDemo(TestCase):
    device = get_first_connected_device()

    def xx_test_build(self):
        folder_of_app = "demoProjects/SampleApp"
        le_android = init_PyAnaDroid(folder_of_app)
        app_projects = le_android.load_projects()
        for app_proj in app_projects:
            app_name = os.path.basename(app_proj)
            print("Processing app " + app_name + " in " + app_proj)
            original_proj = AndroidProject(projname=app_name, projdir=app_proj)
            original_proj.clean_trasformations()
            instrumented_proj_dir = le_android.instrumenter.instrument(original_proj, instr_type=le_android.instrumentation_type)
            instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir, results_dir=le_android.results_dir)
            builder = le_android.init_builder(instr_proj)
            builder.build()
            self.assertTrue(builder.was_last_build_successful())

    def _test_hunter_instrumentation(self, instr_type=INSTRUMENTATION_TYPE.ANNOTATION ):
        folder_of_app = "demoProjects/SampleApp"
        le_android = init_PyAnaDroid(folder_of_app)
        app_projects = le_android.load_projects()
        for app_proj in app_projects:
            app_name = os.path.basename(app_proj)
            print("Processing app " + app_name + " in " + app_proj)
            original_proj = AndroidProject(projname=app_name, projdir=app_proj)
            original_proj.clean_trasformations()
            instrumented_proj_dir = le_android.instrumenter.instrument(original_proj,
                                                                       instr_type=le_android.instrumentation_type)
            instr_proj = AndroidProject(projname=app_name, projdir=instrumented_proj_dir,
                                        results_dir=le_android.results_dir)

            classes = mega_find(instr_proj.proj_dir, pattern="*.java", type_file='f')
            classes += mega_find(instr_proj.proj_dir, pattern="*.kt", type_file='f')
            has_annotations = next(x for x in classes if cat(x) | grep("@HunterDebug"))
            self.assertIsNotNone(has_annotations)

