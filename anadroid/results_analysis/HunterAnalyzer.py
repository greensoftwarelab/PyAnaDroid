from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
import os

class HunterAnalyzer(AbstractAnalyzer):

    def __init__(self):
        super(HunterAnalyzer, self).__init__()
        #self.bin_cmd = "java -jar " + (DEFAULT_JAR_PATH if jarpath is None else jarpath)
        #self.remote_url = remote_url
        #self.aux_analyzer = ApkAPIAnalyzer()

    def setup(self, **kwargs):
        pass

    def show_results(self, app_list):
        pass

    def analyze(self, app, output_log_file="hunter.log", **kwargs):
        hunter_results_out = app.curr_local_dir + '/results/hunter'
        hunter_logs = [f for f in os.listdir(hunter_results_out) if os.path.isfile(os.path.join(hunter_results_out, f))]

        between_tests = 0
        with open(hunter_results_out + "/" + output_log_file, 'w') as outfile:
            for fname in hunter_logs:
                path_file = hunter_results_out + '/' + fname
                with open(path_file) as infile:
                    size = os.path.getsize(path_file)
                    for line in infile:
                        size -= len(line)
                        if not size and between_tests < (len(hunter_logs) - 1):
                            line_aux = line.rstrip()
                            outfile.write(line_aux + ';\n')
                        else:
                            outfile.write(line)
                    between_tests += 1

    def analyze_apis(self):
        return

    def clean(self):
        pass