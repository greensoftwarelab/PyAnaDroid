from manafa.hunter_emanafa import HunterEManafa
import os

from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer


class ManafaAnalyzer(AbstractAnalyzer):
    def __init__(self, profiler):
        super(ManafaAnalyzer, self).__init__()
        self.profiler = profiler

    def setup(self, **kwargs):
        pass

    def show_results(self, app_list):
        pass

    # def analyze(self, app, output_log_file="hunter.log"):
    def analyze(self, app, output_log_file="hunter.log", **kwargs):
        #total, per_component, metrics = self.profiler.manafa.getConsumptionInBetween()
        hunter_trace = {}
        if isinstance(self.profiler.manafa, HunterEManafa):
            # hunter_trace = self.profiler.manafa.hunter.trace
            results_dir = app.curr_local_dir
            hunter_logs = []
            for f in os.listdir(results_dir):
                if "hunter" in f:
                    hunter_logs.append(os.path.join(results_dir, f))

            final_hunter = results_dir + "/" + output_log_file

            # concat all hunter logs on final hunter
            between_tests = 0
            with open(final_hunter, 'w') as outfile:
                for fname in hunter_logs:
                    with open(fname) as infile:
                        size = os.path.getsize(fname)
                        for line in infile:
                            size -= len(line)
                            if not size and between_tests < (len(hunter_logs) - 1):
                                line_aux = line.rstrip()
                                outfile.write(line_aux + ';\n')
                            else:
                                outfile.write(line)
                        between_tests += 1

            # concat all consumption logs on final consumption
            consumption_logs = []
            for f in os.listdir(results_dir):
                if "consumption" in f:
                    consumption_logs.append(os.path.join(results_dir, f))

            final_consumption = results_dir + "/consumption.log"
            interval_line = "------------------------------------------\n"
            with open(final_consumption, 'w') as file:
                file.write(interval_line.join([open(i).read() for i in consumption_logs]))

    def clean(self):
        pass