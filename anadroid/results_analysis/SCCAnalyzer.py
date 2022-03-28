import os

from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
from anadroid.utils.Utils import execute_shell_command, log_to_file


class SCCAnalyzer(AbstractAnalyzer):
    """Implements AbstractAnalyzer interface to allow to calculate app code results using scc tool.
    """
    def __init__(self, profiler):
        super(SCCAnalyzer, self).__init__(profiler)
        self.bin_cmd = "scc"

    def setup(self, **kwargs):
        pass

    def analyze(self, app, output_log_file="scc.log", **kwargs):
        input_dir = app.proj.proj_dir
        cmd = f"{self.bin_cmd} {input_dir} -f json"
        res = execute_shell_command(cmd)
        if res.validate(Exception(f"Unable to analyze sources with {self.bin_cmd}")):
            log_to_file(res.output, output_log_file)

    def show_results(self, app_list):
        pass

    def clean(self):
        pass

    def get_val_for_filter(self, filter_name, add_data=None):
        return super().get_val_for_filter(filter_name, add_data)

    def analyze_tests(self, app, results_dir=None, **kwargs):
        base_dir = app.local_res if results_dir is None else results_dir
        output_file = os.path.join(base_dir, 'scc.log')
        self.analyze(app, output_file, **kwargs)

    def analyze_test(self, app, test_id, **kwargs):
        pass

    def validate_test(self, app, arg1, **kwargs):
        return True

    def validate_filters(self):
        return super().validate_filters()