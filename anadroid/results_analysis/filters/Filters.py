import json
from anadroid.results_analysis.filters.Filter import Filter, is_valid_filter


class Filters(object):
    def __init__(self, supported_filters, filter_file):
        self.filter_file = filter_file
        self.filters = {}
        self.__load_filters(supported_filters)

    def __load_filters(self, supported_filters):
        cfg={}
        with open(self.filter_file, 'r') as jj:
            cfg = json.load(jj)
        for f, v in cfg.items():
            if is_valid_filter(f):
                filterino = Filter(f, v)
                if filterino.name in supported_filters:
                    self.filters[filterino.name] = [] if filterino not in self.filters else self.filters[filterino]
                    self.filters[filterino.name].append(filterino)

    def apply_filter(self, filter_name, val):
        if filter_name in self.filters:
            for flt in self.filters[filter_name]:
                if not flt.apply_filter(val):
                    return False
        return True

    def __str__(self):
        return str(self.filters)
