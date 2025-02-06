import os.path

from anadroid.Anadroid import AnaDroid
from anadroid.analysis.pre_build_analysis.EcoAndroidAnalysis import EcoAndroidAnalysis
from anadroid.application.AndroidProject import AndroidProject
from anadroid.device.MockedDevice import MockedDevice


class MyCustomAnaDroidWorkflow(AnaDroid):
    def default_workflow(self):
        super().default_workflow()




if __name__ == '__main__':
    proj_dir = os.path.join('/Users/rar9993/repos/pyanadroid', "demoProjects/SampleApp")
    needs_dynamic_execution = False
    anad = MyCustomAnaDroidWorkflow(arg1=proj_dir,
                    testing_framework=None,
                    device=MockedDevice(),
                    profiler=None,
                    instrumenter=None,
                    )
    #anad.just_build_apps()
    proj = AndroidProject('SampleApp', proj_dir)
    eco = EcoAndroidAnalysis()
    eco.analyze_project(proj, kwargs={'output_dir': 'output', 'profile_path': proj_dir + 'Project_Default.xml'})
