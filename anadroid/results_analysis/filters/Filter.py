


from manafa.utils.Logger import log, LogSeverity

DEFAULT_FILTER_SEPARATOR = "__"


def is_valid_filter(filter_id, separator=DEFAULT_FILTER_SEPARATOR):
    if separator not in filter_id:
        log(f"invalid filter {filter_id}. Not follows format <filter-name>{separator}<operator>")
        return False
    return True


class Filter(object):
    def __init__(self, filter_id, value, separator=DEFAULT_FILTER_SEPARATOR):
        self.name=""
        self.operator=""
        self.__infer_name_and_separator(filter_id, separator)
        self.val = value

    def __str__(self):
        return f'{self.name} {self.operator} {self.val}'

    def __infer_name_and_separator(self, filter_id, separator):
        if separator not in filter_id:
            log(f"invalid filter {filter_id}. Not follows format <filter-name>{separator}<operator>")
            return None, None
        res = filter_id.split(separator)
        self.name, self.operator = res[0], res[1]

    def apply_filter(self, cmp_val, allow_nulls=False):
        if cmp_val is None:
            return allow_nulls
        if self.operator == 'eq':
            return self.val == cmp_val
        elif self.operator == 'neq':
            return self.val != cmp_val
        elif self.operator == 'ge':
            return cmp_val >= self.val
        elif self.operator == 'gt':
            return cmp_val > self.val
        elif self.operator == 'le':
            return cmp_val <= self.val
        elif self.operator == 'lt':
            return cmp_val < self.val
        elif self.operator == 'in':
            return cmp_val in self.val
        elif self.operator == 'nin':
            return cmp_val not in self.val
        else:
            log("unsupported filter")
            return None