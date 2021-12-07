from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
#from src.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
#from src.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
#from src.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
from anadroid.results_analysis.ApkAPIAnalyzer import ApkAPIAnalyzer
from anadroid.results_analysis.SCCAnalyzer import SCCAnalyzer
from anadroid.utils.Utils import execute_shell_command
from shutil import copy

DEFAULT_JAR_PATH = "resources/jars/AnaDroidAnalyzer.jar"



class OldAnaDroidAnalyzer(AbstractAnalyzer):

    def __init__(self, jarpath=None, remote_url=None):
        super(OldAnaDroidAnalyzer, self).__init__()
        self.bin_cmd = "java -jar " + (DEFAULT_JAR_PATH if jarpath is None else jarpath)
        self.remote_url = "NONE" if remote_url is None else remote_url
        #self.aux_analyzer = ApkAPIAnalyzer()
        self.inner_analyzers = [SCCAnalyzer(), ApkAPIAnalyzer()]

    def setup(self, **kwargs):
        pass

    def inner_analyze(self, app, instr_proj, test_orient, test_framework, output_log_file="AnaDroidAnalyzer.out"):
        for analyzer in self.inner_analyzers:
            if isinstance(analyzer, SCCAnalyzer):
                analyzer.analyze(instr_proj.proj_dir, test_orient, test_framework, output_log_file=app.local_res + "/scc.log")
            elif isinstance(analyzer, ApkAPIAnalyzer):
                analyzer.analyze(app.apk, app.package_name)


    def analyze(self, app, instr_proj, test_orient, test_framework, output_log_file="AnaDroidAnalyzer.out"):
        self.inner_analyze( app, instr_proj, test_orient, test_framework, output_log_file="AnaDroidAnalyzer.out")
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


    def analyze_apis(self):
        pass

    def clean(self):
        pass