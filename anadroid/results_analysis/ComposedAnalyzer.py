from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
import os

class ComposedAnalyzer(AbstractAnalyzer):
    def __init__(self, inner_analyzers=()):
        super(ComposedAnalyzer, self).__init__()
        self.inner_analyzers =[]
        for inn in inner_analyzers:
            if isinstance(inn, AbstractAnalyzer):
                self.inner_analyzers.append(inn)

    def setup(self, **kwargs):
        for inn in self.inner_analyzers:
            inn.setup(**kwargs)

    def analyze(self, app, **kwargs):
        for inn in self.inner_analyzers:
            inn.analyze(app, **kwargs)

    def clean(self):
        for inn in self.inner_analyzers:
            inn.clean()

    def show_results(self, app_list):
        for inn in self.inner_analyzers:
            inn.show_results(app_list)
