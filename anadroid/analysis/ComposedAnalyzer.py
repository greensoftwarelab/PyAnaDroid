from anadroid.analysis.ExecutionResultsAnalyzer import ExecutionResultsAnalyzer


class ComposedAnalyzer(ExecutionResultsAnalyzer):
    """Provides a way to abstract the usage of a set of AbstractAnalyzers through a single api call."""
    def __init__(self, profiler, inner_analyzers=()):
        super(ComposedAnalyzer, self).__init__(profiler)
        self.inner_analyzers = []
        for inn in inner_analyzers:
            if isinstance(inn, ExecutionResultsAnalyzer):
                self.inner_analyzers.append(inn)

    def setup(self, **kwargs):
        for inn in self.inner_analyzers:
            inn.setup(**kwargs)

    def clean(self):
        for inn in self.inner_analyzers:
            inn.clean()

    def show_results(self, app_list):
        for inn in self.inner_analyzers:
            inn.show_results(app_list)

    def analyze_tests(self, app=None, results_dir=None, **kwargs):
        print(self.inner_analyzers)
        for inn in self.inner_analyzers:
            inn.analyze_tests(app, results_dir, **kwargs)

    def analyze_test(self, test_id, **kwargs):
        for inn in self.inner_analyzers:
            inn.analyze_test(test_id, **kwargs)

    def validate_test(self, app, arg1,  **kwargs):
        for inn in self.inner_analyzers:
            if not inn.validate_test(app, arg1, **kwargs):
                return False
        return True

    def validate_filters(self):
        for inn in self.inner_analyzers:
            if not inn.validate_filters():
                return False
        return True

    def get_val_for_filter(self, filter_name, add_data=None):
        return super().get_val_for_filter(filter_name, add_data)

    def analyze_app(self, app, **kwargs):
        for inn in self.inner_analyzers:
            inn.analyze_app(app, **kwargs)