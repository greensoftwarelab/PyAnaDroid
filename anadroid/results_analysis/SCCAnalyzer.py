from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
from anadroid.utils.Utils import execute_shell_command, log_to_file


class SCCAnalyzer(AbstractAnalyzer):
    def __init__(self, ):
        super(SCCAnalyzer, self).__init__()
        self.bin_cmd = "scc"

    def setup(self, **kwargs):
        pass

    def analyze(self, input_dir, test_orient, test_framework, output_log_file="scc.log"):
        cmd = f"{self.bin_cmd} {input_dir}"
        res = execute_shell_command(cmd)
        if res.validate(Exception(f"Unable to analyze sources with {self.bin_cmd}")):
            log_to_file(res.output, output_log_file)


    def clean(self):
        pass