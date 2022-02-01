import json

from manafa.utils.Logger import log, LogSeverity

from anadroid.results_analysis.filters.Filter import Filter, is_valid_filter


class Filters(object):
    def __init__(self, analyzer_class, filter_file):
        self.analyzer_id = analyzer_class
        self.filter_file = filter_file
        self.filters = {}
        self.__load_filters()

    def __load_filters(self):
        cfg={}
        with open(self.filter_file, 'r') as jj:
            cfg = json.load(jj)
        if self.analyzer_id not in cfg:
            return
        anal_filters = cfg[self.analyzer_id]
        for f, v in anal_filters.items():
            if is_valid_filter(f):
                filterino = Filter(f, v)
                self.filters[filterino.name] = [] if filterino not in self.filters else self.filters[filterino]
                self.filters[filterino.name].append(filterino)

    def apply_filter(self, filter_name, val):
        if filter_name in self.filters:
            for flt in self.filters[filter_name]:
                if not flt.apply_filter(val):
                    return False
        return True

    def __str__(self):
        return self.analyzer_id + ":" + str(self.filters)