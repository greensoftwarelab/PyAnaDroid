import json
import os

from anadroid.results_analysis.AbstractAnalyzer import AbstractAnalyzer
from anadroid.utils.Utils import loge, mega_find, logi


class ManafaMethodCoverageAnalyzer(AbstractAnalyzer):
    """Implements AbstractAnalyzer interface to allow analyze  results with EManafa profiler.
    Calculate statistics about the produced results to analyze, validate and characterize executions.
    """
    def __init__(self, profiler):
        self.supported_filters = {"method_coverage"}
        super(ManafaMethodCoverageAnalyzer, self).__init__(profiler)
        self.app_methods = {}
        self.functions = {}

    def setup(self, **kwargs):
        pass

    def show_results(self, app_list):
        pass

    def analyze_test(self, app, test_id, **kwargs):
        pass

    # def analyze(self, app, output_log_file="hunter.log"):
    def analyze_tests(self, app, results_dir=None, **kwargs):
        pass

    def validate_test(self, app, test_id, **kwargs):
        self.get_test_stats(app, test_id)
        return self.validate_filters_for_test(test_id)

    def clean(self):
        self.app_methods = []
        self.functions = {}

    def get_test_stats(self, app, test_id):
        self.app_methods = self.__get_app_methods(app) if len(self.app_methods) == 0 else self.app_methods
        self.functions[str(test_id)] = self.__get_functions_consumption_of_test(app, test_id)

    def __get_functions_consumption_of_test(self, app, test_id, index_file="tests_index.json", lookup_str="functions_"):
        functions = {}
        test_id = str(test_id)
        if not os.path.exists(os.path.join(app.curr_local_dir, index_file)):
            return functions
        with open(os.path.join(app.curr_local_dir, index_file), 'r') as j:
            idx_content = json.load(j)
        res = [x for x in idx_content[test_id] if lookup_str in x]
        if len(res) == 0 or not os.path.exists(res[0]):
            return functions
        with open(res[0], 'r') as j:
            functions = json.load(j)
        return functions

    @staticmethod
    def __get_app_methods(app):
        app_methods = {}
        app_methods_candidates = [x for x in mega_find(os.path.join(app.local_res, "all"), type_file='f', maxdepth=1) if "allMethods.json" not in x]
        if len(app_methods_candidates) > 0:
            app_methods_file = app_methods_candidates[0]
            with open(app_methods_file, 'r') as j:
                app_methods = json.load(j)
        else:
            loge("all_methods.json file not found")
        methods = []
        for da_class, class_obj in app_methods.items():
            if 'class_methods' not in class_obj:
                continue
            for method in class_obj['class_methods'].keys():
                methods.append(class_obj['class_methods'][method])
        return methods

    def validate_filters(self):
        for filter_name, fv in self.validation_filters.filters.items():
            if filter_name in self.supported_filters:
                for filt in fv:
                    val_for_filter = self.get_val_for_filter(filter_name)
                    if not filt.apply_filter(val_for_filter):
                        loge(f"filter {filter_name} failed. value: {val_for_filter}")
                        return False
            else:
                loge(f"unsupported filter {filter_name}")
                return False
        return True

    def validate_filters_for_test(self, test_id):
        for filter_name, fv in self.validation_filters.filters.items():
            if filter_name in self.supported_filters:
                for filt in fv:
                    val_for_filter = self.get_val_for_filter(filter_name, test_id)
                    if not filt.apply_filter(val_for_filter):
                        loge(f"filter {filter_name} failed. value: {val_for_filter}")
                        return False
            else:
                loge(f"unsupported filter {filter_name}")
                return False
        return True

    def get_val_for_filter(self, filter_name, add_data=None):
        test_id = str( add_data if add_data is not None else 0 )
        if filter_name == "method_coverage":
            res = 0
            if test_id in self.functions:
                coverage_pct = (len(self.functions[test_id]) / len(self.app_methods)) if len(self.app_methods) > 0 else 0
                return coverage_pct
        val = super().get_val_for_filter(filter_name, test_id)
        if val is None:
            loge(f"unsupported value ({val}) for {filter_name} ({self.__class__})")
        return val