from src.results_analysis.AbstractAnalyzer import AbstractAnalyzer
from src.utils.Utils import execute_shell_command

DEFAULT_JAR_PATH = "resources/jars/AnaDroidAnalyzer.jar"


class AnaDroidAnalyzer(AbstractAnalyzer):

    def __init__(self, jarpath=None, remote_url=None):
        super(AnaDroidAnalyzer, self).__init__()
        self.bin_cmd = "java -jar " + (DEFAULT_JAR_PATH if jarpath is None else jarpath)
        self.remote_url = remote_url

    def setup(self, **kwargs):
        pass

    def analyze(self, input_dir, test_orient, test_framework, output_log_file="AnaDroidAnalyzer.out"):
        cmd = "{bin_prefix} {test_orient} \"{input_dir}\" {test_framework} {remote_repo_url} {output_log_file}"
        cmd.format(
            bin_prefix=self.bin_cmd,
            test_orient=test_orient,
            test_framework=test_framework,
            remote_repo_url=self.remote_url,
            output_log_file = output_log_file
        )
        # java -jar $GD_ANALYZER $trace "$projLocalDir/" $monkey $GREENSOURCE_URL 2>&1 | tee "$temp_folder/analyzerResult.out"
        res = execute_shell_command(cmd)
        res.validate(Exception("Analyzer error"))

    def clean(self):
        pass