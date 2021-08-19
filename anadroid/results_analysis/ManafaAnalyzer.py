from manafa.hunter_emanafa import HunterEManafa

from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer


class ManafaAnalyzer(AbstractAnalyzer):
    def __init__(self, profiler):
        super(ManafaAnalyzer, self).__init__()
        self.profiler = profiler

    def setup(self, **kwargs):
        pass

    def analyze(self, res_dir, test_orient, test_framework, output_log_file="report.json"):
        a, b, c = self.profiler.manafa.getConsumptionInBetween()
        d={}
        if isinstance(self.profiler, HunterEManafa):
            d = self.profiler.manafa.hunter.trace

        print(a)
        print(b)
        print(c)
        print(d)

    def clean(self):
        pass