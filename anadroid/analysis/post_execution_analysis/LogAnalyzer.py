import os

from logcatparser.logCatParser import LogCatParser

from anadroid.analysis.ExecutionResultsAnalyzer import ExecutionResultsAnalyzer
from anadroid.utils.Utils import loge
from manafa.utils.Logger import log


class LogAnalyzer(ExecutionResultsAnalyzer):
    """Implements AbstractAnalyzer interface to allow analyze Android logs produced during profiling sessions using
    logcatparser.
    Calculate statistics about the produced logs to analyze and characterize test executions.
    """
    def __init__(self, profiler):
        self.supported_filters = {"fatal_errors", "ANR", "Exceptions"}
        super(LogAnalyzer, self).__init__(profiler)
        self.logcatparser = LogCatParser(log_format="threadtime")

    def setup(self, **kwargs):
        super().setup()

    def fetch_log_files(self, dir_path, test_id=""):
        #return os.path.join(app.curr_local_dir, f'test_{test_id}.logcat') TODO fetch test file name format from cfg file
        return [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f'{test_id}.logcat' in f]

    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        target_dir = app.curr_local_dir if results_dir is None and app is not None else results_dir
        for log_file in self.fetch_log_files(target_dir):
            test_id = kwargs['test_id'] if 'test_id' in kwargs else os.path.basename(log_file).split("_")[1].split(".")[0]
            self.analyze_test(app, log_file, output_filename=f'test_{test_id}_logresume.json')
            self.clean()

    def analyze_test(self, app, log_file, output_filename=None, **kwargs):
        self.logcatparser.parse_file(log_file)
        the_dir = os.path.dirname(log_file)
        self.logcatparser.save_results(os.path.join(the_dir, output_filename))

    def clean(self):
        super().clean()
        self.logcatparser = LogCatParser(log_format="threadtime")

    def show_results(self, app_list):
        #for analyzed_app in app_list:
        #print(analyzed_app)
        #print("loganalyzer TODO show result for each test")
        pass

    def validate_test(self, app, test_id, **kwargs):
        log_file = kwargs.get('log_filename') if 'log_filename' in kwargs else 'batata' # todo
        self.logcatparser.parse_file(log_file)
        return self.validate_filters()

    def validate_filters(self):
        for filter_name, fv in self.validation_filters.filters.items():
            if filter_name in self.supported_filters:
                for filt in fv:
                    val_for_filter = self.get_val_for_filter(filter_name, )
                    if not filt.apply_filter(val_for_filter):
                        log(f"filter {filter_name} failed. value: {val_for_filter}")
                        return False
            else:
                log(f"unsupported filter {filter_name}")
                return False
        return True

    def get_val_for_filter(self, filter_name, add_data=None):
        if filter_name == "fatal_errors":
            return self.logcatparser.get_parser_resume()['stats']['fatal']
        elif filter_name == "ANR":
            return self.logcatparser.get_parser_resume()['known_errors']['ANR']
        elif filter_name == "Exceptions":
            return self.logcatparser.get_parser_resume()['known_errors']['Exception']
        val = super().get_val_for_filter(filter_name, add_data)
        if val is None:
            loge(f"unsupported value ({val}) for {filter_name} ({self.__class__})")
        return val

    def analyze_app(self, app, **kwargs):
        pass