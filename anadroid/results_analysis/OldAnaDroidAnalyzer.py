import os

from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
#from src.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
#from src.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
#from src.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
from anadroid.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
from anadroid.results_analysis.SCCAnalyzer import SCCAnalyzer
from anadroid.utils.Utils import execute_shell_command, get_resources_dir
from shutil import copy, copyfile

DEFAULT_JAR_PATH = os.path.join(get_resources_dir(), "jars", "AnaDroidAnalyzer.jar")


class OldAnaDroidAnalyzer(AbstractAnalyzer):
    """Implements AbstractAnalyzer interface to allow analyze profiled results with Trepn  profiler.
    Calculate statistics about the produced results to analyze, validate and characterize executions.
    """
    def __init__(self, profiler, jarpath=None, remote_url=None):
        super(OldAnaDroidAnalyzer, self).__init__(profiler)
        self.bin_cmd = "java -jar " + (DEFAULT_JAR_PATH if jarpath is None else jarpath)
        self.remote_url = "NONE" if remote_url is None else remote_url
        self.inner_analyzers = [] #[ApkAPIAnalyzer(profiler)]

    def setup(self, **kwargs):
        pass

    def show_results(self, app_list):
        pass

    def inner_analyze(self, app, output_log_file="AnaDroidAnalyzer.out", **kwargs):
        instr_proj = app.proj
        test_orient = kwargs.get("instr_type")
        for analyzer in self.inner_analyzers:
            if isinstance(analyzer, SCCAnalyzer):
                analyzer.analyze(instr_proj.proj_dir, test_orient, output_log_file=os.path.join(app.local_res, "scc.json"))
            elif isinstance(analyzer, ApkAPIAnalyzer):
                filename = analyzer.analyze(app.apk, app.package_name)
                target_dir = os.path.join(app.local_res, "all")
                copyfile(filename, os.path.join(target_dir,  os.path.basename(filename)))

    def analyze(self, app, **kwargs):
        test_framework = kwargs.get("testing_framework")
        test_orient = kwargs.get("instr_type")
        output_log_file = kwargs.get("output_log_file") if 'output_log_file' in kwargs else "oldanadroid_output.log"
        self.inner_analyze(app, **kwargs)
        cmd = "{bin_prefix} -{test_orient} \"{input_dir}\" -{test_framework} {remote_repo_url} > {output_log_file}".format(
            bin_prefix=self.bin_cmd,
            test_orient=test_orient.value,
            input_dir=app.local_res,
            test_framework=test_framework.id.value,
            remote_repo_url=self.remote_url,
            output_log_file=output_log_file
        )
        # java -jar $GD_ANALYZER $trace "$projLocalDir/" $monkey $GREENSOURCE_URL 2>&1 | tee "$temp_folder/analyzerResult.out"
        print(cmd)
        res = execute_shell_command(cmd)
        res.validate(Exception("Analyzer error"))
        print(res)

    def get_val_for_filter(self, filter_name, add_data=None):
        return super().get_val_for_filter(filter_name, add_data)

    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        self.analyze(app, **kwargs)

    def analyze_test(self, app, test_id, **kwargs):
        pass

    def validate_test(self, app, arg1, **kwargs):
        if app is None:
            return True
        for inn in self.inner_analyzers:
            if not inn.validate_test(app, arg1):
                return False
        return True

    def validate_filters(self):
        for inn in self.inner_analyzers:
            if not inn.validate_filters():
                return False
        return True

    def clean(self):
        pass