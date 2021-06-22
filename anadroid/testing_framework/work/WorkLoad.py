from anadroid.testing_framework.work.AbstractWorkLoad import AbstractWorkLoad


class WorkLoad(AbstractWorkLoad):
    def __init__(self):
        super(WorkLoad, self).__init__()
        self.work_units = []
        self.w_index = 0

    def add_unit(self, wunit):
        self.work_units.append(wunit)

    def consume(self):
        val = self.work_units[self.w_index] if len(self.work_units) > self.w_index else None
        self.w_index += 1
        return val

    def flush(self):
        self.work_units.clear()
        self.w_index = 0