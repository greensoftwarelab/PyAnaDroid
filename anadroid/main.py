from anadroid.Anadroid import AnaDroid
from anadroid.Types import TESTING_FRAMEWORK, PROFILER
from anadroid.application.AndroidProject import BUILD_TYPE
from anadroid.instrument.Types import INSTRUMENTATION_TYPE


def init_defaultPyAnaDroid(apps_dir):
    return AnaDroid(apps_dir=apps_dir,
                      testing_framework=TESTING_FRAMEWORK.MONKEY,
                      profiler=PROFILER.MANAFA,
                      build_type=BUILD_TYPE.DEBUG,
                      instrumentation_type=INSTRUMENTATION_TYPE.ANNOTATION
    )


if __name__ == '__main__':
    folder_of_apps = "demoProjects/SampleApp"
    anadroid = init_defaultPyAnaDroid(folder_of_apps)
    anadroid.defaultWorkflow()
    #anadroid.just_build_apps()
