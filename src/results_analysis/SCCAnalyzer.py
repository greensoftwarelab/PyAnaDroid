from src.results_analysis.AbstractAnalyzer import AbstractAnalyzer
from src.utils.Utils import execute_shell_command


class SCCAnalyzer(AbstractAnalyzer):
    def __init__(self, ):
        super(SCCAnalyzer, self).__init__()
        self.bin_cmd = "scc"

    def setup(self, **kwargs):
        pass

    def analyze(self, input_dir, test_orient, test_framework, output_log_file="scc.log"):
        cmd = f"{self.bin_cmd} {input_dir}"
        execute_shell_command(cmd).validate(
            Exception(f"Unable to analyze sources with {self.bin_cmd}"))

    def clean(self):
        pass