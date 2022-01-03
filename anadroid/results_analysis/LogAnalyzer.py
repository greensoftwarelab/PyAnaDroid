from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
from anadroid.utils.Utils import execute_shell_command


class LogAnalyzer(AbstractAnalyzer):
    def __init__(self):
        super(LogAnalyzer, self).__init__()

    def setup(self, **kwargs):
        super().setup()

    def analyze(self, app, output_log_file="test-undefined.log", **kwargs):
        # analyze logs and not do this : execute_shell_command("adb logcat -d > ", args=[output_log_file])
        pass

    def clean(self):
        super().setup()

    def show_results(self, app_list):
        pass
